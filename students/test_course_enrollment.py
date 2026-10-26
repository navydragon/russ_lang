import json
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from courses.models import Course, Lesson, Task, TaskAttempt
from . import portal, roster
from .forms import GroupForm
from .importing import HEADERS
from .models import Group, Student


class EnrollmentServiceTests(TestCase):
    def setUp(self):
        self.a = Course.objects.create(name='Курс А', websoft_id='101')
        self.b = Course.objects.create(name='Курс Б', websoft_id='102')
        self.group = Group.objects.create(name='Группа', code='RU')
        self.group.courses.add(self.a)
        self.assignments = set()
        self.calls = []
        self.fail_for = None
        self.lost_response = False
        self.api = patch('students.portal.call', side_effect=self.remote).start()
        self.addCleanup(patch.stopall)
        self.client.force_login(get_user_model().objects.create_user(username='staff', is_staff=True))

    def remote(self, action, data, method='POST'):
        self.calls.append((action, data))
        if action == 'upsert_group':
            return {'status': 'unchanged', 'group_id': '800'}
        if action == 'upsert_student':
            return {'status': 'unchanged', 'student_id': '900' + data['code']}
        if action == 'ensure_membership':
            return {'status': 'unchanged', 'group_id': '800', 'student_id': '900' + data['student_code']}
        if action == 'ensure_course_assignments':
            changed = False
            for course_id in data['course_ids']:
                pair = (data['student_code'], course_id)
                if pair == self.fail_for:
                    raise portal.PortalError('Курс WebSoft ' + course_id + ' не подтверждён', 'assignment_failed', uncertain=True)
                changed |= pair not in self.assignments
                self.assignments.add(pair)
            if self.lost_response:
                self.lost_response = False
                raise portal.PortalError('Ответ потерян', uncertain=True)
            return {'status': 'updated' if changed else 'unchanged', 'student_id': '900' + data['student_code']}
        return {'status': 'removed'}

    def data(self, code='001'):
        return dict(code=code, last_name='Фамилия', first_name='Имя', middle_name='', email='')

    def student(self, code='001'):
        return Student.objects.create(code=code, last_name='Фамилия', first_name='Имя', group=self.group)

    def form(self, courses):
        self.group.refresh_from_db()
        form = GroupForm({'name': self.group.name, 'code': self.group.code, 'courses': [c.pk for c in courses]}, instance=self.group)
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def test_save_and_repeat_assign_all_courses(self):
        self.group.courses.add(self.b)
        obj, status = roster.save_student(self.group.pk, self.data())
        self.assertEqual(status, 'updated')
        again, status = roster.save_student(self.group.pk, self.data(), student_id=obj.pk)
        self.assertEqual(status, 'unchanged')
        self.assertEqual(obj.pk, again.pk)
        self.assertEqual(self.assignments, {('001', '101'), ('001', '102')})

    def test_empty_course_set_keeps_legacy_behavior(self):
        self.group.courses.clear()
        roster.save_student(self.group.pk, self.data())
        self.assertFalse(any(action == 'ensure_course_assignments' for action, _ in self.calls))

    def test_invalid_mapping_rejected_before_any_network(self):
        self.a.websoft_id = None
        self.a.save()
        with self.assertRaisesMessage(portal.PortalError, 'Курс А'):
            roster.save_student(self.group.pk, self.data())
        self.api.assert_not_called()

    def test_group_assigns_courses_to_existing_students(self):
        self.student('001')
        self.student('002')
        roster.save_group(self.form([self.a, self.b]))
        self.assertEqual(self.assignments, {('001', '101'), ('001', '102'), ('002', '101'), ('002', '102')})
        self.assertEqual(set(self.group.courses.values_list('pk', flat=True)), {self.a.pk, self.b.pk})

    def test_group_failure_preserves_last_confirmed_set_and_retry_repairs(self):
        self.student('001')
        self.student('002')
        self.fail_for = ('002', '102')
        with self.assertRaisesMessage(portal.PortalError, '002'):
            roster.save_group(self.form([self.a, self.b]))
        self.assertEqual(list(self.group.courses.all()), [self.a])
        self.assertIn(('001', '102'), self.assignments)
        self.fail_for = None
        roster.save_group(self.form([self.a, self.b]))
        self.assertIn(('002', '102'), self.assignments)
        self.assertEqual(self.group.courses.count(), 2)

    def test_remove_course_does_not_revoke_and_new_student_uses_current_set(self):
        self.student()
        roster.save_group(self.form([self.a, self.b]))
        roster.save_group(self.form([self.a]))
        self.assertIn(('001', '102'), self.assignments)
        roster.save_student(self.group.pk, self.data('002'))
        self.assertNotIn(('002', '102'), self.assignments)
        self.assertFalse(any('revoke' in action or 'delete_learning' in action for action, _ in self.calls))

    def test_lost_response_then_retry_commits_student_without_duplicate_assignment(self):
        self.lost_response = True
        with self.assertRaises(portal.PortalError):
            roster.save_student(self.group.pk, self.data())
        self.assertFalse(Student.objects.exists())
        roster.save_student(self.group.pk, self.data())
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(self.assignments, {('001', '101')})

    def test_database_failure_after_assignment_and_result_preservation(self):
        student = self.student()
        lesson = Lesson.objects.create(name='Урок', course=self.a)
        task = Task.objects.create(name='Задание', lesson=lesson)
        attempt = TaskAttempt.objects.create(student=student, task=task, datetime=timezone.now(), results='preserve')
        with patch('students.roster.Student.objects.update_or_create', side_effect=OperationalError('database error')):
            with self.assertRaises(portal.PortalError):
                roster.save_student(self.group.pk, self.data())
        roster.save_student(self.group.pk, self.data())
        roster.remove_student(self.group.pk, student.pk)
        self.assertTrue(TaskAttempt.objects.filter(pk=attempt.pk, results='preserve').exists())
        self.assertEqual(self.assignments, {('001', '101')})

    def test_unbound_course_form_and_group_failure_preserve_selection(self):
        invalid = Course.objects.create(name='Без привязки')
        response = self.client.post(reverse('students:group_edit', args=[self.group.pk]), {'name': 'Группа', 'code': 'RU', 'courses': [invalid.pk]})
        self.assertContains(response, 'укажите корректный ID WebSoft')
        self.api.assert_not_called()
        self.student()
        self.fail_for = ('001', '102')
        response = self.client.post(reverse('students:group_edit', args=[self.group.pk]), {'name': 'Группа', 'code': 'RU', 'courses': [self.a.pk, self.b.pk]})
        self.assertContains(response, '001')
        self.assertContains(response, 'Курс Б')
        self.assertEqual(set(map(int, response.context['form']['courses'].value())), {self.a.pk, self.b.pk})
        self.assertEqual(list(self.group.courses.all()), [self.a])

    def test_import_assignment_error_then_safe_repeat(self):
        book = Workbook()
        book.active.append(HEADERS)
        book.active.append(['Фамилия', 'Имя', '', '', '001', '001', ''])
        stream = BytesIO()
        book.save(stream)
        content = stream.getvalue()
        url = reverse('students:student_import', args=[self.group.pk])
        self.fail_for = ('001', '101')
        token = self.client.post(url, {'file': SimpleUploadedFile('test.xlsx', content)}).json()['token']
        request = lambda: self.client.post(url, {'file': SimpleUploadedFile('test.xlsx', content), 'phase': 'execute', 'token': token}).json()
        first = request()
        self.assertEqual(first['results'][0]['status'], 'uncertain')
        self.assertIn('101', first['results'][0]['message'])
        self.assertFalse(Student.objects.exists())
        self.fail_for = None
        self.assertEqual(request()['results'][0]['status'], 'updated')
        self.assertEqual(request()['results'][0]['status'], 'unchanged')


@override_settings(PORTAL_ROSTER_URL='http://127.0.0.1/_wt', PORTAL_ROSTER_TOKEN='test')
class EnrollmentResponseTests(TestCase):
    def request(self):
        return {'group_code': 'RU', 'student_code': '001', 'course_ids': ['101']}

    def response(self, **overrides):
        return {'status': 'unchanged', 'complete': True, 'student_id': '900001', 'assignments': [{'course_id': '101', 'learning_id': '9223372036854775800', 'status': 'unchanged'}], **overrides}

    @patch('students.portal.build_opener')
    def test_valid_response_and_large_string_id(self, opener):
        opener.return_value.open.return_value = BytesIO(json.dumps({'ok': True, 'data': self.response()}).encode())
        result = portal.call('ensure_course_assignments', self.request())
        self.assertEqual(result['assignments'][0]['learning_id'], '9223372036854775800')

    def test_missing_duplicate_unknown_numeric_and_partial_results(self):
        invalid = [
            self.response(assignments=[]),
            self.response(assignments=self.response()['assignments'] * 2),
            self.response(assignments=[{'course_id': '102', 'learning_id': '9', 'status': 'unchanged'}]),
            self.response(assignments=[{'course_id': '101', 'learning_id': 9, 'status': 'created'}]),
            self.response(complete=False, assignments=[{'course_id': '101', 'status': 'error', 'message': 'private remote exception'}]),
            self.response(complete='true'),
        ]
        for result in invalid:
            with self.subTest(result=result), self.assertRaises(portal.PortalError) as caught:
                portal.validate_assignments(self.request(), result)
            self.assertNotIn('private remote exception', str(caught.exception))
