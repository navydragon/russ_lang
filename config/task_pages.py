"""Раздача HTML-уроков из каталога tasks/ по HTTP (не file://)."""
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.urls import re_path
from django.views.static import serve

TASKS_DIR = Path(settings.BASE_DIR) / 'tasks'

_ALLOWED_SUFFIXES = {'.html', '.js', '.css', '.map'}


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
