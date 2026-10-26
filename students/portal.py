"""Server-only JSON adapter. Never include remote bodies or credentials in errors."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from django.conf import settings
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables
from courses.websoft import validate_websoft_id


class PortalError(Exception):
    def __init__(self, message, code='portal_error', uncertain=False):
        super().__init__(message)
        self.code = code
        self.uncertain = uncertain


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@sensitive_variables()
def call(action, data, method='POST'):
    url = settings.PORTAL_ROSTER_URL
    parts = urlsplit(url)
    local_http = parts.scheme == 'http' and parts.hostname in {'127.0.0.1', 'localhost', '::1'}
    if (parts.scheme != 'https' and not local_http) or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment or not settings.PORTAL_ROSTER_TOKEN:
        raise PortalError('Подключение к порталу не настроено.', 'configuration')
    if parts.path.rstrip('/').endswith('/_wt'):
        endpoint = url.rstrip('/') + '/russian_language/action/' + action
    else:
        # Retain direct-file routing for local contract tests and old settings.
        endpoint = url + '?' + urlencode({'mode': 'russian_language', 'action': action})
    request = Request(
        endpoint,
        data=json.dumps(data, ensure_ascii=False).encode('utf-8'), method=method,
        headers={'Authorization': settings.PORTAL_ROSTER_TOKEN, 'Content-Type': 'application/json; charset=utf-8'},
    )
    try:
        with build_opener(NoRedirect).open(request, timeout=settings.PORTAL_ROSTER_TIMEOUT) as response:
            body = json.loads(response.read(1024 * 1024).decode('utf-8-sig'))
    except HTTPError as exc:
        messages = {400: 'Портал отклонил данные.', 401: 'Ошибка авторизации портала.', 403: 'Нет прав интеграции на портале.', 409: 'Конфликт данных портала. Проверьте код и состав группы.'}
        raise PortalError(messages.get(exc.code, 'Портал недоступен. Повторите операцию.'), str(exc.code), exc.code >= 500) from None
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError):
        raise PortalError('Ответ портала не получен. Результат неизвестен; безопасно повторите операцию.', uncertain=True) from None
    if not isinstance(body, dict) or body.get('ok') is not True or not isinstance(body.get('data'), dict):
        raise PortalError('Некорректный ответ портала; повторите операцию.', uncertain=True)
    result = body['data']
    if result.get('status') not in {'created', 'updated', 'unchanged', 'removed'}:
        raise PortalError('Некорректный статус портала.', uncertain=True)
    for key in ('group_id', 'student_id'):
        if key in result and (not isinstance(result[key], str) or not result[key].isdigit() or len(result[key]) > 32):
            raise PortalError('Некорректный идентификатор портала.', uncertain=True)
    required = {'upsert_group': ('group_id',), 'upsert_student': ('student_id',), 'ensure_membership': ('group_id', 'student_id')}
    if any(key not in result for key in required.get(action, ())):
        raise PortalError('Неполный ответ портала.', uncertain=True)
    if action == 'ensure_course_assignments':
        validate_assignments(data, result)
    return result


def validate_assignments(request_data, result):
    expected = set(request_data['course_ids'])
    rows = result.get('assignments')
    if type(result.get('complete')) is not bool or not isinstance(rows, list) or not isinstance(result.get('student_id'), str):
        raise PortalError('Неполный ответ о назначении курсов. Повторите операцию.', uncertain=True)
    seen, errors = set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise PortalError('Некорректный результат назначения курсов.', uncertain=True)
        course_id = row.get('course_id')
        if not isinstance(course_id, str) or course_id not in expected or course_id in seen:
            raise PortalError('Некорректный список назначений. Повторите операцию.', uncertain=True)
        seen.add(course_id)
        if row.get('status') == 'error':
            errors.append(course_id)
        elif row.get('status') not in {'created', 'unchanged'} or not isinstance(row.get('learning_id'), str) or not row['learning_id'].isascii() or not row['learning_id'].isdigit():
            raise PortalError('Некорректный идентификатор обучения.', uncertain=True)
        else:
            try:
                validate_websoft_id(row['learning_id'])
            except ValidationError:
                raise PortalError('Некорректный идентификатор обучения.', uncertain=True) from None
    if seen != expected:
        raise PortalError('Портал подтвердил не все курсы. Повторите операцию.', uncertain=True)
    if result['complete'] is not True or errors:
        failed = errors or list(expected)
        raise PortalError('Не подтверждено назначение курсов WebSoft: ' + ', '.join(failed) + '. Часть назначений могла выполниться; повторите операцию.', 'assignment_failed', uncertain=True)
