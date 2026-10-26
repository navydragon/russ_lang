"""Opt-in integration test using ONLY codex-roster-* fixtures on local WebSoft.

The temporary integration account and allowlist must be prepared by the developer.
No production settings, database or credentials are used. The opener rewrites only
the known test host to loopback HTTP so the production adapter remains HTTPS-only.
"""
import base64
import os
import sys
from pathlib import Path
from urllib.request import Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.roster_test_settings'

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.test.utils import setup_databases, teardown_databases, setup_test_environment
from django.urls import reverse
from openpyxl import Workbook
from io import BytesIO
from students import portal
from students.models import Group, Student


class LoopbackOpener:
    def __init__(self):
        self.opener = build_opener(portal.NoRedirect)

    def open(self, request, timeout):
        if not request.full_url.startswith('https://roster-test.invalid/'):
            raise ValueError('Unexpected target')
        local = Request(request.full_url.replace('https://roster-test.invalid', 'http://127.0.0.1', 1), data=request.data, headers=dict(request.header_items()), method=request.method)
        return self.opener.open(local, timeout=timeout)


def main():
    from students.importing import HEADERS
    token = base64.b64encode(b'codex-roster-student-20261026:test-roster-random-c91284').decode()
    setup_test_environment()
    old = setup_databases(verbosity=0, interactive=False)
    try:
        with override_settings(PORTAL_ROSTER_URL='https://roster-test.invalid/api/index.html', PORTAL_ROSTER_TOKEN=token), patch('students.portal.build_opener', return_value=LoopbackOpener()):
            client = Client()
            client.force_login(get_user_model().objects.create_user(username='roster-test-admin', is_staff=True))
            response = client.post(reverse('students:group_create'), {'code': 'codex-roster-test-20261026', 'name': 'Русский — проверка'})
            assert response.status_code == 302, response.content[:200]
            group = Group.objects.get(code='codex-roster-test-20261026')
            data = {'code': 'codex-roster-target-20261026', 'last_name': 'Проверочный', 'first_name': 'Студент', 'email': 'target@example.test', 'password': 'fixture-target-pw-8e173'}
            create = reverse('students:student_create', args=[group.pk])
            real_call = portal.call
            lost_once = False
            def lose_response(action, payload, method='POST'):
                nonlocal lost_once
                result = real_call(action, payload, method)
                if action == 'ensure_membership' and not lost_once:
                    lost_once = True
                    raise portal.PortalError('Simulated lost response after remote commit', uncertain=True)
                return result
            with patch('students.portal.call', side_effect=lose_response):
                assert client.post(create, data).status_code == 400
            assert not Student.objects.exists()
            assert client.post(create, data).json()['ok']
            student = Student.objects.get(code=data['code'])
            data['first_name'] = 'Изменённый'
            assert client.post(reverse('students:student_edit', args=[group.pk, student.pk]), data).json()['ok']
            book = Workbook()
            book.active.append(HEADERS)
            book.active.append(['Проверочный', 'Импорт', '', 'target@example.test', data['code'], data['code'], 'must-not-change'])
            stream = BytesIO()
            book.save(stream)
            content = stream.getvalue()
            url = reverse('students:student_import', args=[group.pk])
            for _ in range(2):
                preview = client.post(url, {'file': SimpleUploadedFile('students.xlsx', content)}).json()
                assert 'password' not in preview['rows'][0]
                result = client.post(url, {'file': SimpleUploadedFile('students.xlsx', content), 'phase': 'execute', 'token': preview['token']}).json()
                assert result['results'][0]['status'] in {'updated', 'unchanged'}, result
            assert Student.objects.count() == 1
            assert client.post(reverse('students:remove_student_from_group', args=[group.pk, student.pk])).status_code == 302
            student.refresh_from_db()
            assert student.group_id is None
            assert client.post(reverse('students:group_delete', args=[group.pk])).status_code == 302
            assert not Group.objects.exists()
            print('PASS: Django UI -> HTTP adapter -> WebSoft: group, remote commit/lost response/retry, student, edit, XLSX twice, exclude, delete empty group')
    finally:
        teardown_databases(old, verbosity=0)


if __name__ == '__main__':
    main()
