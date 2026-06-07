"""
Builds the WebRTC ICE server list (STUN + optional TURN) for a video call.

Precedence (first configured wins):
  1. metered.ca API — set METERED_DOMAIN + METERED_API_KEY. We fetch the iceServers
     (with short-lived TURN credentials) from metered's API and cache them briefly.
     This is the recommended free path (metered's free tier ~50 GB/month).
  2. coturn ephemeral HMAC — set TURN_URLS + TURN_STATIC_AUTH_SECRET. We mint
     short-lived credentials with the standard `use-auth-secret` scheme.
  3. static TURN — set TURN_URLS + TURN_USERNAME + TURN_CREDENTIAL.
  4. STUN only (fine on many networks; add TURN for mobile / strict firewalls).

Credentials are generated/fetched per call (served via /video/<room>/ice/), so
nothing long-lived is baked into the page.
"""
import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from django.conf import settings

# Tiny in-process cache for the metered API result (creds are valid for hours).
_metered_cache = {'servers': None, 'expires': 0.0}


def _stun_only():
    return [{'urls': settings.STUN_URLS}] if settings.STUN_URLS else []


def _fetch_metered():
    """Fetch iceServers from metered.ca, cached for TURN_TTL seconds."""
    now = time.time()
    if _metered_cache['servers'] is not None and now < _metered_cache['expires']:
        return _metered_cache['servers']

    url = (f"https://{settings.METERED_DOMAIN}/api/v1/turn/credentials"
           f"?apiKey={urllib.parse.quote(settings.METERED_API_KEY)}")
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            servers = json.loads(resp.read().decode('utf-8'))
        if isinstance(servers, list) and servers:
            _metered_cache['servers'] = servers
            _metered_cache['expires'] = now + max(60, settings.TURN_TTL)
            return servers
    except Exception:
        pass
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
    # 1. metered.ca API (returns its own STUN + TURN list).
    if settings.METERED_DOMAIN and settings.METERED_API_KEY:
        return _fetch_metered()

    servers = _stun_only()

    # 2 / 3. self-managed TURN.
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
