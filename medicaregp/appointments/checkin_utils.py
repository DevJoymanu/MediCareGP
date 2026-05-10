import hmac
import hashlib
from datetime import date
from django.conf import settings
from django.core.cache import cache


def generate_daily_token():
    today = date.today().isoformat()
    secret = settings.SECRET_KEY.encode()
    return hmac.new(secret, today.encode(), hashlib.sha256).hexdigest()


def validate_daily_token(token):
    return hmac.compare_digest(token or '', generate_daily_token())


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def check_ip_rate_limit(ip_address):
    """Returns True if under limit, False if exceeded (max 3 per 15 min per IP)."""
    key = f'checkin_ip_{ip_address}'
    count = cache.get(key, 0)
    if count >= 3:
        return False
    cache.set(key, count + 1, 60 * 15)
    return True


def check_id_rate_limit(id_number):
    """Returns True if under limit, False if exceeded (max 2 pending per ID per day)."""
    from .models import CheckInRequest
    from django.utils import timezone
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = CheckInRequest.objects.filter(
        id_number=id_number,
        status='pending',
        created_at__gte=today_start,
    ).count()
    return count < 2


def expire_old_requests():
    """Mark pending requests older than 2 hours as expired."""
    from .models import CheckInRequest
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=2)
    CheckInRequest.objects.filter(status='pending', created_at__lt=cutoff).update(status='expired')


def validate_geolocation(lat, lng):
    """
    Returns True if geolocation is disabled (in settings) or coordinates are
    within CHECKIN_RADIUS_METRES of the practice. Returns False otherwise.
    """
    if not settings.CHECKIN_GEOLOCATION_ENABLED:
        return True
    if lat is None or lng is None:
        return False
    import math
    practice_lat = settings.CHECKIN_PRACTICE_LAT
    practice_lng = settings.CHECKIN_PRACTICE_LNG
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(practice_lat), math.radians(lat)
    dphi = math.radians(lat - practice_lat)
    dlambda = math.radians(lng - practice_lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    distance = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return distance <= settings.CHECKIN_RADIUS_METRES
