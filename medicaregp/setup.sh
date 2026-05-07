#!/bin/bash
pip install django>=4.2
cd "$(dirname "$0")"
python manage.py makemigrations patients appointments consultations scripts
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@medicaregp.com','admin123')" | python manage.py shell
echo ""
echo "✅ Setup complete! Run: python manage.py runserver 0.0.0.0:8000"
echo "   Login: admin / admin123"
