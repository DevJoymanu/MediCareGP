import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-medicaregp-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
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

# Give SQLite up to 30 seconds to acquire a write lock before raising
# "database is locked" — eliminates contention errors at low concurrency.
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default'].setdefault('OPTIONS', {})['timeout'] = 30
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

# ── Media storage: Cloudflare R2 (S3-compatible) ───────────────────────────────
# Railway's filesystem is ephemeral, so uploaded files (lab/radiology results,
# documents) must live in object storage. When the R2_* env vars are set, all
# media FileFields use the R2 bucket; otherwise media falls back to the local
# disk (handy for local development).
#
# Required env vars on Railway:
#   R2_ACCESS_KEY_ID        — R2 API token access key
#   R2_SECRET_ACCESS_KEY    — R2 API token secret
#   R2_BUCKET_NAME          — e.g. medicaregp-media
#   R2_ENDPOINT_URL         — https://<account-id>.r2.cloudflarestorage.com
# Optional:
#   R2_CUSTOM_DOMAIN        — public CDN domain if the bucket is served publicly
#   R2_SIGNED_URL_EXPIRE    — seconds a signed URL stays valid (default 3600)
USE_R2 = bool(os.environ.get('R2_BUCKET_NAME') and os.environ.get('R2_ACCESS_KEY_ID'))

if USE_R2:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID       = os.environ['R2_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY   = os.environ['R2_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['R2_BUCKET_NAME']
    AWS_S3_ENDPOINT_URL     = os.environ['R2_ENDPOINT_URL']
    AWS_S3_REGION_NAME      = 'auto'           # R2 ignores region but boto3 needs a value
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL         = None             # R2 has no ACLs — must be None
    AWS_S3_FILE_OVERWRITE   = False            # keep distinct uploads, never clobber

    # Patient result files are sensitive: keep the bucket private and serve via
    # short-lived signed URLs (links expire — POPIA-friendly). Set a public
    # custom domain only if you intentionally make the bucket public.
    _r2_domain = os.environ.get('R2_CUSTOM_DOMAIN')
    if _r2_domain:
        AWS_S3_CUSTOM_DOMAIN = _r2_domain
        AWS_QUERYSTRING_AUTH = False
    else:
        AWS_QUERYSTRING_AUTH    = True
        AWS_QUERYSTRING_EXPIRE  = int(os.environ.get('R2_SIGNED_URL_EXPIRE', '3600'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allow our own pages to be framed (the doctor's video room embeds the
# consultation form in an iframe). SAMEORIGIN still blocks external sites.
X_FRAME_OPTIONS = 'SAMEORIGIN'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Staff session timeout: sign out after 2 hours of inactivity. Because the
# session is re-saved on every request (SESSION_SAVE_EVERY_REQUEST), the 2-hour
# window slides forward while the user is active — so an idle session expires,
# but an in-progress consultation (whose page keeps making requests) stays alive.
SESSION_COOKIE_AGE = 2 * 60 * 60          # 7200 seconds = 2 hours
SESSION_SAVE_EVERY_REQUEST = True

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

# ── Patient self check-in ─────────────────────────────────────────────────────
CHECKIN_URL_TOKEN          = os.environ.get('CHECKIN_URL_TOKEN', 'gp-checkin-k7x9mq')
CHECKIN_GEOLOCATION_ENABLED = False
CHECKIN_PRACTICE_LAT       = float(os.environ.get('CHECKIN_PRACTICE_LAT', '0'))
CHECKIN_PRACTICE_LNG       = float(os.environ.get('CHECKIN_PRACTICE_LNG', '0'))
CHECKIN_RADIUS_METRES      = 300
CHECKIN_OPEN_HOUR          = 7
CHECKIN_CLOSE_HOUR         = 18

# ── Practice details (used on invoices & emails) ───────────────────────────────
PRACTICE_NAME    = 'Dr. Tamuka Chivonivoni'
PRACTICE_SUBTITLE = 'General Practitioner'
PRACTICE_EMAIL   = 'dr.chivonivoni@gpcrm.co.za'
PRACTICE_PHONE   = '+27 21 555 0100'
PRACTICE_ADDRESS = (
    'Shop B7, Ekhaya Medical Centre<br/>'
    'Ekhaya Mall, Kwa-Thema<br/>'
    'Springs, Gauteng<br/>'
    'South Africa'
)
PRACTICE_REG     = 'HPCSA: MP 0123456'
VAT_RATE         = 15   # percentage

# ── Healthbridge / BHF claim submission ────────────────────────────────────────
# Set these to the practice number issued by Healthbridge.
# The doctor should retrieve this from their Healthbridge account.
PRACTICE_NUMBER           = os.environ.get('PRACTICE_NUMBER', 'MP0123456')
HEALTHBRIDGE_PRACTICE_NO  = os.environ.get('HEALTHBRIDGE_PRACTICE_NO', PRACTICE_NUMBER)

# ── Public website (Medical-Flow) — bookable time slots ────────────────────────
# The website offers these discrete slots; a slot is "taken" once any Appointment
# OR WebBooking occupies that exact date+time, so website bookings and CRM
# appointments can never clash. No payment is taken — a booking is just a request
# that reception confirms into an appointment.
BOOKING_SLOT_MINUTES = 30
BOOKING_HOURS = [('09:30', '12:00'), ('13:00', '17:30')]   # (start, end) per period, end exclusive

# ── Online (video) consultations — built-in WebRTC ─────────────────────────────
# The appointment-type string that marks a booking as an online video visit.
# Must match APPOINTMENT_TYPES in the React BookingForm.tsx.
ONLINE_CONSULT_TYPE = 'Online Consultation (Video call)'

# ICE servers the browsers use to connect peer-to-peer (see appointments/turn.py,
# which builds the list per call). STUN (free, public) is enough on many networks;
# a TURN server is needed for reliability behind strict NATs / mobile / firewalls.
#
#   STUN_URLS                 comma-separated, default Google STUN
#   TURN_URLS                 comma-separated, e.g. "turn:turn.host:3478,turns:turn.host:5349"
#   TURN_STATIC_AUTH_SECRET   coturn `use-auth-secret` → short-lived HMAC creds (recommended)
#   TURN_USERNAME/CREDENTIAL  static long-lived creds (alternative to the secret)
#   TURN_TTL                  lifetime (seconds) of generated ephemeral creds
STUN_URLS = [u.strip() for u in os.environ.get('STUN_URLS', 'stun:stun.l.google.com:19302').split(',') if u.strip()]
TURN_URLS = [u.strip() for u in os.environ.get('TURN_URLS', '').split(',') if u.strip()]
TURN_STATIC_AUTH_SECRET = os.environ.get('TURN_STATIC_AUTH_SECRET', '')
TURN_USERNAME   = os.environ.get('TURN_USERNAME', '')
TURN_CREDENTIAL = os.environ.get('TURN_CREDENTIAL', '')
TURN_TTL = int(os.environ.get('TURN_TTL', '3600'))

# metered.ca free TURN (recommended): create an app at metered.ca, then set
#   METERED_DOMAIN   e.g. "yourapp.metered.live"
#   METERED_API_KEY  from the metered dashboard
# The app fetches fresh ICE servers + short-lived TURN credentials from their API.
METERED_DOMAIN  = os.environ.get('METERED_DOMAIN', '')
METERED_API_KEY = os.environ.get('METERED_API_KEY', '')

# Cloudflare Realtime TURN (recommended — 1 TB/month free, no server to run).
# Create a TURN key at dash.cloudflare.com → Realtime → TURN, then set:
#   CLOUDFLARE_TURN_KEY_ID      the Turn Key ID
#   CLOUDFLARE_TURN_API_TOKEN   the key's API token
# The app mints short-lived ICE credentials from Cloudflare's API per call.
CLOUDFLARE_TURN_KEY_ID    = os.environ.get('CLOUDFLARE_TURN_KEY_ID', '')
CLOUDFLARE_TURN_API_TOKEN = os.environ.get('CLOUDFLARE_TURN_API_TOKEN', '')
