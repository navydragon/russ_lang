"""Opt-in local integration check. Requires owned enrollment_fixture.html fixtures.

Usage: python scripts/check_group_course_websoft.py .test-venv/enrollment-fixtures.json
Only the configured loopback API and fixed test-code namespace are accepted.
Uses an isolated Django test database, never the user's local application data.
"""
import json
import os
import sys
import time
from pathlib import Path
from io import BytesIO
from urllib.parse import urlsplit
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.roster_test_settings'
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test.utils import setup_databases, teardown_databases, setup_test_environment
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from courses.models import Course, Lesson, Task, TaskAttempt
from students import portal, roster
from students.forms import GroupForm
from students.importing import HEADERS
from students.models import Group, Student


def main():
    fixture = json.loads(Path(sys.argv[1]).read_text())
    if urlsplit(settings.PORTAL_ROSTER_URL).hostname != '127.0.0.1' or fixture['group_code'] != 'codex-enrollment-group-20261026':
        raise RuntimeError('Only owned local fixtures allowed')
    setup_test_environment()
    old = setup_databases(verbosity=0, interactive=False)
    try:
        courses = [Course.objects.create(name=f'Fixture course {index}', websoft_id=course_id) for index, course_id in enumerate(fixture['course_ids'])]
        form = GroupForm({'name': 'Enrollment local integration', 'code': fixture['group_code'], 'courses': [courses[0].pk]})
        assert form.is_valid(), form.errors
        group = roster.save_group(form)
        students = []
        for index in range(20):
            students.append(Student.objects.create(code=f'codex-enrollment-student-{index}-20261026', last_name='Fixture', first_name=str(index), group=group))
        lesson = Lesson.objects.create(course=courses[0], name='Fixture')
        task = Task.objects.create(lesson=lesson, name='Fixture')
        attempt = TaskAttempt.objects.create(student=students[0], task=task, datetime=timezone.now(), results='preserve')

        def group_form(selected):
            group.refresh_from_db()
            form = GroupForm({'name': group.name, 'code': group.code, 'courses': [course.pk for course in selected]}, instance=group)
            assert form.is_valid(), form.errors
            return form

        real_call = portal.call
        lost = False
        def lose_response(action, data, method='POST'):
            nonlocal lost
            result = real_call(action, data, method)
            if action == 'ensure_course_assignments' and data['student_code'] == students[5].code and not lost:
                lost = True
                raise portal.PortalError('Simulated lost response after remote assignment', uncertain=True)
            return result
        with patch('students.portal.call', side_effect=lose_response):
            try:
                roster.save_group(group_form(courses))
                raise AssertionError('Expected an unconfirmed assignment')
            except portal.PortalError:
                pass
        assert list(group.courses.all()) == [courses[0]]
        started = time.monotonic()
        roster.save_group(group_form(courses))
        elapsed = time.monotonic() - started
        assert group.courses.count() == 2

        client = Client()
        client.force_login(get_user_model().objects.create_user(username='fixture-staff', is_staff=True))
        book = Workbook()
        book.active.append(HEADERS)
        book.active.append(['Fixture', 'Импорт', '', '', students[3].code, students[3].code, 'ignored-existing-password'])
        stream = BytesIO()
        book.save(stream)
        content = stream.getvalue()
        url = reverse('students:student_import', args=[group.pk])
        for _ in range(2):
            preview = client.post(url, {'file': SimpleUploadedFile('fixture.xlsx', content)}).json()
            result = client.post(url, {'file': SimpleUploadedFile('fixture.xlsx', content), 'phase': 'execute', 'token': preview['token']}).json()
            assert result['results'][0]['status'] in {'updated', 'unchanged'}, result
        assert Student.objects.count() == 20
        roster.save_group(group_form([courses[0]]))
        assert list(group.courses.all()) == [courses[0]]
        roster.save_student(group.pk, {'code':'codex-enrollment-student-20-20261026', 'last_name':'Fixture', 'first_name':'After removal', 'email':''})
        roster.remove_student(group.pk, students[0].pk)
        assert TaskAttempt.objects.get(pk=attempt.pk).results == 'preserve'
        # Restore test membership for auditing the archived learning.
        portal.call('ensure_membership', {'group_code':group.code, 'student_code':students[0].code})
        print(json.dumps({'passed':True, 'students':20, 'courses':2, 'recovery_group_save_seconds':round(elapsed,3), 'lost_response_recovered':True, 'repeat_import_no_duplicates':True, 'local_results_preserved':True, 'post_removal_student_created':True}))
    finally:
        teardown_databases(old, verbosity=0)


if __name__ == '__main__':
    main()
