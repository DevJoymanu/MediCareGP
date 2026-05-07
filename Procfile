web: cd medicaregp && gunicorn medicaregp.wsgi --bind 0.0.0.0:$PORT --workers 2
release: cd medicaregp && python manage.py migrate --no-input && python manage.py collectstatic --no-input
