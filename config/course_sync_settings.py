"""Явный профиль БД из .env для синхронизации курса; локальный сервер не затрагивает."""
import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403

_engine = os.getenv('DB_ENGINE', '').strip()
if _engine not in ('postgres', 'postgresql', 'django.db.backends.postgresql'):
    raise ImproperlyConfigured('Для синхронизации заполните DB_ENGINE=postgres в .env.')
if not os.getenv('DB_NAME') or not os.getenv('DB_USER'):  # noqa: F405
    raise ImproperlyConfigured('Для синхронизации заполните DB_NAME и DB_USER в .env.')

_options = {'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10'))}  # noqa: F405
if os.getenv('DB_SSLMODE'):  # noqa: F405
    _options['sslmode'] = os.environ['DB_SSLMODE']  # noqa: F405

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ['DB_NAME'],  # noqa: F405
    'USER': os.environ['DB_USER'],  # noqa: F405
    'PASSWORD': os.getenv('DB_PASSWORD', ''),  # noqa: F405
    'HOST': os.getenv('COURSE_SYNC_DB_HOST') or os.getenv('DB_HOST', 'localhost'),
    'PORT': os.getenv('COURSE_SYNC_DB_PORT') or os.getenv('DB_PORT', '5432'),
    'OPTIONS': _options,
}}
# Этот профиль не предоставляет страницу с подменой student_code.
DEBUG = False
