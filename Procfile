web: cd medicaregp && gunicorn medicaregp.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120
release: cd medicaregp && python manage.py migrate --no-input && python manage.py collectstatic --no-input
