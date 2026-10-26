"""Isolated URL configuration avoids unrelated pre-existing merge conflicts."""
from .settings import *

ROOT_URLCONF = 'config.roster_test_urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
