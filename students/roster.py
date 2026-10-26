"""Portal first, local commit second; retries reconcile by immutable code."""
import hashlib
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, transaction
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.views.decorators.debug import sensitive_variables

from . import portal
from .models import Group, Student
from courses.websoft import validate_websoft_id


@contextmanager
def roster_lock():
    # OS lock survives multiple workers and is released on process termination.
    namespace = hashlib.sha256(str(settings.BASE_DIR).encode()).hexdigest()[:20]
    path = Path(tempfile.gettempdir()) / ('russ-roster-' + namespace + '.lock')
    with open(path, 'a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if not stream.tell():
            stream.write(b'0')
            stream.flush()
        deadline = time.monotonic() + 2
        acquired = False
        try:
            while not acquired:
                stream.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except OSError:
                    if time.monotonic() >= deadline:
                        raise portal.PortalError('Другая операция ещё выполняется. Повторите запрос.', 'busy') from None
                    time.sleep(.05)
            yield
        finally:
            if acquired:
                stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def operation():
    with roster_lock():
        try:
            yield
        except DatabaseError:
            raise portal.PortalError('Локальное сохранение не завершено. Безопасно повторите операцию.', uncertain=True) from None


def save_group(form):
    with operation():
        obj = form.instance
        if obj.pk and Group.objects.get(pk=obj.pk).code != form.cleaned_data['code']:
            raise portal.PortalError('Код существующей группы менять нельзя.', 'validation')
        courses = list(form.cleaned_data.get('courses', []))
        course_ids(courses)
        remote = portal.call('upsert_group', {'code': form.cleaned_data['code'], 'name': form.cleaned_data['name']})
        desired = Group(pk=obj.pk, code=form.cleaned_data['code'], name=form.cleaned_data['name'])
        if courses and obj.pk:
            for student in Student.objects.filter(group_id=obj.pk).order_by('pk'):
                fields = {key: getattr(student, key) or '' for key in ('code', 'last_name', 'first_name', 'middle_name', 'email')}
                try:
                    _save_student(desired, fields, courses=courses, group_remote=remote)
                except portal.PortalError as exc:
                    raise portal.PortalError(f'Студент {student.code}: {exc}', exc.code, exc.uncertain) from None
        with transaction.atomic():
            # A repeat of group creation after a lost response attaches the same record.
            group, _ = Group.objects.update_or_create(code=form.cleaned_data['code'], defaults={'name': form.cleaned_data['name'], 'portal_id': remote['group_id']})
            group.curators.set(form.cleaned_data['curators'])
            group.courses.set(courses)
        return group


def validate_membership(code, group):
    existing = Student.objects.filter(code=code).first()
    if existing and existing.group_id not in (None, group.pk):
        raise portal.PortalError('Студент состоит в другой группе. Сначала исключите его из неё.', 'other_group')
    return existing


@sensitive_variables()
def save_student(group_id, data, student_id=None):
    with operation():
        group = Group.objects.get(pk=group_id)
        return _save_student(group, data, student_id=student_id)


def course_ids(courses):
    ids = []
    for course in courses:
        try:
            if not course.websoft_id:
                raise ValidationError('Нет ID')
            validate_websoft_id(course.websoft_id)
        except ValidationError:
            raise portal.PortalError(f'Курс «{course.name}»: укажите корректный ID WebSoft в каталоге курсов.', 'invalid_course') from None
        ids.append(course.websoft_id)
    return ids


@sensitive_variables()
def _save_student(group, data, student_id=None, courses=None, group_remote=None):
    code = data['code']
    if student_id is not None:
        obj = Student.objects.get(pk=student_id)
        if obj.code != code or obj.group_id != group.pk:
            raise portal.PortalError('Код или группа студента изменились. Обновите страницу.', 'conflict')
    validate_membership(code, group)
    courses = list(group.courses.all()) if courses is None else courses
    ids = course_ids(courses)
    fields = {key: data.get(key, '') or '' for key in ('last_name', 'first_name', 'middle_name', 'email')}
    gr = group_remote or portal.call('upsert_group', {'code': group.code, 'name': group.name})
    remote = portal.call('upsert_student', {**fields, 'code': code, 'login': code, 'password': data.get('password') or get_random_string(24)})
    membership = portal.call('ensure_membership', {'group_code': group.code, 'student_code': code})
    if membership['group_id'] != gr['group_id'] or membership['student_id'] != remote['student_id']:
        raise portal.PortalError('Идентификаторы портала не совпали. Повторите операцию.', uncertain=True)
    assignment_status = 'unchanged'
    if ids:
        try:
            assignments = portal.call('ensure_course_assignments', {'group_code': group.code, 'student_code': code, 'course_ids': ids})
            if assignments['student_id'] != remote['student_id']:
                raise portal.PortalError('Идентификатор студента при назначении не совпал.', uncertain=True)
            assignment_status = assignments['status']
        except portal.PortalError as exc:
            names = ', '.join(f'{course.name} ({course.websoft_id})' for course in courses)
            raise portal.PortalError(f'Студент {code}, курсы {names}: {exc}', exc.code, exc.uncertain) from None
    with transaction.atomic():
        validate_membership(code, group)
        Group.objects.filter(pk=group.pk).update(portal_id=gr['group_id'])
        student, _ = Student.objects.update_or_create(code=code, defaults={**fields, 'group_id': group.pk, 'portal_id': remote['student_id']})
    status = remote['status']
    if status == 'unchanged' and (membership['status'] != 'unchanged' or assignment_status != 'unchanged'):
        status = 'updated'
    return student, status


def remove_student(group_id, student_id):
    with operation():
        group = Group.objects.get(pk=group_id)
        student = Student.objects.get(pk=student_id)
        if student.group_id not in (None, group.pk):
            raise portal.PortalError('Студент не принадлежит этой группе.', 'other_group')
        portal.call('remove_membership', {'group_code': group.code, 'student_code': student.code}, method='DELETE')
        Student.objects.filter(pk=student_id, group_id=group_id).update(group=None)


def delete_group(group_id):
    with operation():
        group = Group.objects.get(pk=group_id)
        if group.students.exists():
            raise portal.PortalError('Сначала исключите студентов из группы.', 'group_not_empty')
        portal.call('delete_group', {'code': group.code}, method='DELETE')
        with transaction.atomic():
            group = Group.objects.get(pk=group_id)
            if group.students.exists():
                raise portal.PortalError('Состав группы изменился. Повторите операцию.', 'conflict')
            group.delete()
