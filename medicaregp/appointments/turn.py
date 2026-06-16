"""
Builds the WebRTC ICE server list (STUN + optional TURN) for a video call.

Precedence (first configured wins):
  1. Cloudflare Realtime TURN — set CLOUDFLARE_TURN_KEY_ID + CLOUDFLARE_TURN_API_TOKEN.
     We mint short-lived ICE credentials from Cloudflare's API. Recommended free
     path: 1 TB/month free, no server to run.
  2. metered.ca API — set METERED_DOMAIN + METERED_API_KEY. We fetch the iceServers
     (with short-lived TURN credentials) from metered's API and cache them briefly
     (metered's free tier is only 500 MB/month).
  3. coturn ephemeral HMAC — set TURN_URLS + TURN_STATIC_AUTH_SECRET. We mint
     short-lived credentials with the standard `use-auth-secret` scheme.
  4. static TURN — set TURN_URLS + TURN_USERNAME + TURN_CREDENTIAL.
  5. STUN only (fine on many networks; add TURN for mobile / strict firewalls).

Credentials are generated/fetched per call (served via /video/<room>/ice/), so
nothing long-lived is baked into the page.
"""
import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

# Tiny in-process caches for fetched provider results (creds are valid for hours).
_metered_cache = {'servers': None, 'expires': 0.0}
_cloudflare_cache = {'servers': None, 'expires': 0.0}
# Last fetch errors (for the /video/turn-test/ diagnostics page).
_metered_error = None
_cloudflare_error = None


def _stun_only():
    return [{'urls': settings.STUN_URLS}] if settings.STUN_URLS else []


def _fetch_cloudflare():
    """Mint short-lived ICE servers from Cloudflare Realtime TURN, cached briefly."""
    global _cloudflare_error
    now = time.time()
    if _cloudflare_cache['servers'] is not None and now < _cloudflare_cache['expires']:
        return _cloudflare_cache['servers']

    key_id = settings.CLOUDFLARE_TURN_KEY_ID.strip().split()[0] if settings.CLOUDFLARE_TURN_KEY_ID.strip() else ''
    url = f"https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/credentials/generate-ice-servers"
    # Credentials live for a day; we cache them only for TURN_TTL so a rotated
    # token is picked up promptly.
    data = json.dumps({'ttl': 86400}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': f'Bearer {settings.CLOUDFLARE_TURN_API_TOKEN.strip()}',
            'Content-Type': 'application/json',
            # Cloudflare's edge bot-protection blocks the default Python-urllib
            # User-Agent with HTTP 403 "error code: 1010" — send a normal one.
            'User-Agent': 'MediCareGP/1.0 (+https://medicareapp.up.railway.app)',
        })
        with urllib.request.urlopen(req, timeout=6) as resp:
            body = resp.read().decode('utf-8')
            payload = json.loads(body)
        ice = payload.get('iceServers')
        # Cloudflare returns a single iceServers object; the browser wants a list.
        servers = ice if isinstance(ice, list) else ([ice] if ice else None)
        if servers:
            _cloudflare_cache['servers'] = servers
            _cloudflare_cache['expires'] = now + max(60, settings.TURN_TTL)
            _cloudflare_error = None
            return servers
        _cloudflare_error = f"cloudflare returned no iceServers: {body[:200]!r}"
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8')[:300]
        except Exception:
            detail = ''
        _cloudflare_error = f"HTTP {e.code} {e.reason}: {detail}"
    except Exception as e:
        _cloudflare_error = f"{type(e).__name__}: {e}"
    # On failure, reuse a previous good result if we have one, else STUN only.
    return _cloudflare_cache['servers'] or _stun_only()


def _fetch_metered():
    """Fetch iceServers from metered.ca, cached for TURN_TTL seconds."""
    global _metered_error
    now = time.time()
    if _metered_cache['servers'] is not None and now < _metered_cache['expires']:
        return _metered_cache['servers']

    # METERED_DOMAIN must be a bare host like "myapp.metered.live". Be forgiving:
    # take the first whitespace-delimited token (drops any pasted comment), then
    # strip an accidental scheme / trailing slash / path so the URL is well-formed.
    domain = settings.METERED_DOMAIN.strip().split()[0] if settings.METERED_DOMAIN.strip() else ''
    domain = domain.split('://', 1)[-1].strip('/').split('/', 1)[0]
    url = (f"https://{domain}/api/v1/turn/credentials"
           f"?apiKey={urllib.parse.quote(settings.METERED_API_KEY)}")
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            body = resp.read().decode('utf-8')
            servers = json.loads(body)
        if isinstance(servers, list) and servers:
            _metered_cache['servers'] = servers
            _metered_cache['expires'] = now + max(60, settings.TURN_TTL)
            _metered_error = None
            return servers
        _metered_error = f"metered returned no servers: {body[:200]!r}"
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8')[:300]
        except Exception:
            detail = ''
        _metered_error = f"HTTP {e.code} {e.reason}: {detail}"
    except Exception as e:
        _metered_error = f"{type(e).__name__}: {e}"
    # On failure, reuse a previous good result if we have one, else STUN only.
    return _metered_cache['servers'] or _stun_only()


def _coturn_hmac():
    expiry = int(time.time()) + settings.TURN_TTL
    username = str(expiry)
    digest = hmac.new(settings.TURN_STATIC_AUTH_SECRET.encode('utf-8'),
                      username.encode('utf-8'), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode('ascii')
    return {'urls': settings.TURN_URLS, 'username': username, 'credential': credential}


def build_ice_servers():
    # 1. Cloudflare Realtime TURN (returns its own STUN + TURN list).
    if settings.CLOUDFLARE_TURN_KEY_ID and settings.CLOUDFLARE_TURN_API_TOKEN:
        return _fetch_cloudflare()

    # 2. metered.ca API (returns its own STUN + TURN list).
    if settings.METERED_DOMAIN and settings.METERED_API_KEY:
        return _fetch_metered()

    servers = _stun_only()

    # 3 / 4. self-managed TURN.
    if settings.TURN_URLS:
        if settings.TURN_STATIC_AUTH_SECRET:
            servers.append(_coturn_hmac())
        elif settings.TURN_USERNAME:
            servers.append({
                'urls': settings.TURN_URLS,
                'username': settings.TURN_USERNAME,
                'credential': settings.TURN_CREDENTIAL,
            })

    return servers


def diagnostics():
    """Server-side view of the ICE config, for the staff TURN-test page.

    Credentials are never included — only which env vars are set, which provider
    path was taken, the resulting server URLs, and the last fetch error (if any).
    """
    servers = build_ice_servers()
    urls = []
    for s in servers:
        u = s.get('urls')
        urls.extend(u if isinstance(u, list) else [u])

    if settings.CLOUDFLARE_TURN_KEY_ID and settings.CLOUDFLARE_TURN_API_TOKEN:
        provider = 'cloudflare'
    elif settings.METERED_DOMAIN and settings.METERED_API_KEY:
        provider = 'metered'
    elif settings.TURN_URLS and settings.TURN_STATIC_AUTH_SECRET:
        provider = 'coturn-hmac'
    elif settings.TURN_URLS and settings.TURN_USERNAME:
        provider = 'static-turn'
    else:
        provider = 'stun-only'

    return {
        'provider': provider,
        'env': {
            'CLOUDFLARE_TURN_KEY_ID': bool(settings.CLOUDFLARE_TURN_KEY_ID),
            'CLOUDFLARE_TURN_API_TOKEN': bool(settings.CLOUDFLARE_TURN_API_TOKEN),
            'METERED_DOMAIN': bool(settings.METERED_DOMAIN),
            'METERED_API_KEY': bool(settings.METERED_API_KEY),
            'TURN_URLS': bool(settings.TURN_URLS),
            'TURN_STATIC_AUTH_SECRET': bool(settings.TURN_STATIC_AUTH_SECRET),
            'TURN_USERNAME': bool(settings.TURN_USERNAME),
        },
        'server_urls': urls,
        'has_turn': any('turn:' in (u or '') or 'turns:' in (u or '') for u in urls),
        'metered_error': _metered_error,
        'cloudflare_error': _cloudflare_error,
    }
