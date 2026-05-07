import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-medicaregp-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://medicareapp.up.railway.app').split(',')
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'patients','appointments','consultations','scripts','tasks','billing',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'medicaregp.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','medicaregp.context_processors.global_context']}}]
WSGI_APPLICATION = 'medicaregp.wsgi.application'
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
    },
}

# ── Email ──────────────────────────────────────────────────────────────────────
# Default: console backend (emails printed to terminal — great for development).
# To send real emails swap to smtp and fill in the SMTP_* vars below.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── To use Gmail SMTP, uncomment and fill in: ──────────────────────────────────
# EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST      = 'smtp.gmail.com'
# EMAIL_PORT      = 587
# EMAIL_USE_TLS   = True
# EMAIL_HOST_USER = 'your-gmail@gmail.com'       # sender address
# EMAIL_HOST_PASSWORD = 'your-app-password'       # Gmail App Password (not your login password)
# DEFAULT_FROM_EMAIL  = 'GP CRM <your-gmail@gmail.com>'

# ── Practice details (used on invoices & emails) ───────────────────────────────
PRACTICE_NAME    = 'Dr. Tamuka Chivonivoni'
PRACTICE_SUBTITLE = 'General Practitioner'
PRACTICE_EMAIL   = 'dr.chivonivoni@gpcrm.co.za'
PRACTICE_PHONE   = '+27 21 555 0100'
PRACTICE_ADDRESS = '1 Medical Park, Cape Town, 8001'
PRACTICE_REG     = 'HPCSA: MP 0123456'
VAT_RATE         = 15   # percentage
