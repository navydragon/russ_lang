"""Раздача HTML-уроков из каталога tasks/ по HTTP (не file://)."""
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import re_path
from django.views.static import serve

TASKS_DIR = Path(settings.BASE_DIR) / 'tasks'

_ALLOWED_SUFFIXES = {'.html', '.js', '.css', '.map', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.wav'}

_LEGACY_TASK_PATHS = {
    f'{name}.html': f'lesson1/{name}/{name}.html'
    for name in (
        'city_speaking', 'class_speaking', 'flat_speaking',
        'family_story', 'room_story',
    )
}
_LEGACY_TASK_PATHS['lesson3/university_reading.html'] = (
    'lesson3/university_reading/university_reading.html'
)


def serve_task_file(request, path: str):
    """Отдаёт безопасные файлы из tasks/ (html/js/css), включая вложенные каталоги."""
    if not path or path.startswith('/') or '\\' in path:
        raise Http404('Not found')
    # Normalize separators; reject empty segments and ".."
    parts = Path(path).parts
    if not parts or any(p in ('', '.', '..') for p in parts):
        raise Http404('Not found')
    if Path(path).suffix.lower() not in _ALLOWED_SUFFIXES:
        raise Http404('Not found')

    if path in _LEGACY_TASK_PATHS:
        url = '/tasks/' + _LEGACY_TASK_PATHS[path]
        query = request.META.get('QUERY_STRING', '')
        if query:
            url += '?' + query
        return HttpResponseRedirect(url)

    tasks_root = TASKS_DIR.resolve()
    full = (TASKS_DIR / Path(*parts)).resolve()
    try:
        full.relative_to(tasks_root)
    except ValueError:
        raise Http404('Not found') from None
    if not full.is_file():
        raise Http404('Not found')

    # serve() expects path relative to document_root
    relative = full.relative_to(tasks_root).as_posix()
    return serve(request, relative, document_root=str(tasks_root))


urlpatterns = [
    re_path(r'^tasks/(?P<path>.+)$', serve_task_file, name='serve_task_file'),
]
