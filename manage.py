#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv


def _inject_default_runserver_port():
    if len(sys.argv) < 2 or sys.argv[1] != 'runserver':
        return

    args_after = sys.argv[2:]
    has_addrport = any(not arg.startswith('-') for arg in args_after)
    if has_addrport:
        return

    load_dotenv()
    port = os.getenv('DJANGO_PORT', '8000')
    sys.argv.insert(2, f'127.0.0.1:{port}')


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    _inject_default_runserver_port()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

