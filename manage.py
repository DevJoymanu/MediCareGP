#!/usr/bin/env python
"""Repo-root entrypoint that launches the real Django project."""
import os
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    app_root = project_root / 'medicaregp'
    sys.path.insert(0, str(app_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicaregp.settings')
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
