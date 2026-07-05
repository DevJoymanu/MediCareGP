"""Worked example: a real HTTP scheme adapter for the medaid gateway.

Shows the full shape — timeouts, bounded retries, idempotency, taxonomy
mapping, PHI-free logging. Adapt field names to the actual scheme spec;
the STRUCTURE is the point.

To wire in:
  1. Save as medicaregp/medaid/adapters/<scheme>_rest.py
  2. Register in ADAPTERS (adapters/__init__.py) and SchemeConfig.ADAPTER_CHOICES
  3. Create the SchemeConfig row (endpoint URL + env-var NAMES for creds)
"""
import logging
import time
import uuid

import requests

from medaid.gateway import (ClaimResult, EligibilityResult, MedicalAidGateway,
                            MemberDetails)

log = logging.getLogger('medaid')

TIMEOUT = (5, 30)          # (connect, read) seconds — NEVER omit
RETRIES = 2                # connection errors / 5xx only
BACKOFF = 1.5              # seconds, multiplied per attempt


class ExampleRestAdapter(MedicalAidGateway):
    """Adapter for a JSON-over-HTTPS scheme API."""

    def _headers(self, correlation_id):
        creds = self.config.credentials()          # resolved from env by NAME
        return {
            'Authorization': f"Bearer {creds['api_key']}",
            'X-Correlation-Id': correlation_id,
            'Accept': 'application/json',
        }

    def _call(self, method, path, correlation_id, **kwargs):
        """One HTTP call with bounded retry. Logs metadata, never bodies."""
        url = self.config.endpoint_url.rstrip('/') + path
        last_exc = None
        for attempt in range(RETRIES + 1):
            started = time.monotonic()
            try:
                response = requests.request(
                    method, url, timeout=TIMEOUT,
                    headers=self._headers(correlation_id), **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                log.warning('medaid %s %s attempt=%d error=%s cid=%s',
                            self.config.scheme_name, path, attempt,
                            type(exc).__name__, correlation_id)
                time.sleep(BACKOFF * (attempt + 1))
                continue
            log.info('medaid %s %s status=%d ms=%d cid=%s',
                     self.config.scheme_name, path, response.status_code,
                     (time.monotonic() - started) * 1000, correlation_id)
            if response.status_code >= 500 and attempt < RETRIES:
                time.sleep(BACKOFF * (attempt + 1))
                continue
            return response
        raise UpstreamDown(str(last_exc))

    # ── Interface implementation ──────────────────────────────────────────

    def verify_member(self, member_number, id_number=''):
        cid = uuid.uuid4().hex[:12]
        try:
            r = self._call('GET', f'/members/{member_number}', cid)
        except UpstreamDown:
            return MemberDetails(found=False, status='upstream_down',
                                 message='Scheme not responding — verify manually.')
        if r.status_code == 404:
            return MemberDetails(found=False, status='member_not_found',
                                 message='Member number not recognised — check the card.')
        if not r.ok:
            return MemberDetails(found=False, status='malformed_response',
                                 message=f'Scheme error (ref {cid}).')
        data = r.json()
        # Scheme-specific field names die HERE — normalize to internal shape.
        return MemberDetails(found=True, status='active',
                             member_number=member_number,
                             first_name=data.get('firstName', ''),
                             last_name=data.get('surname', ''),
                             plan=data.get('option', ''))

    def submit_claim(self, claim_payload):
        """claim_payload comes ONLY from ClaimBuilder (whitelist-enforced).
        Idempotency: the claim number doubles as the idempotency key, so a
        retry after a timeout cannot double-submit."""
        cid = uuid.uuid4().hex[:12]
        try:
            r = self._call('POST', '/claims', cid, json=claim_payload,
                           headers_extra={'Idempotency-Key': claim_payload['claim_number']})
        except UpstreamDown:
            return ClaimResult(status='upstream_down', reference='',
                               message=f'Scheme unreachable — queued for manual submission (ref {cid}).')
        if r.status_code in (200, 201, 202):
            body = r.json()
            return ClaimResult(status='accepted', reference=body.get('claimRef', ''),
                               message='Claim accepted by scheme.')
        if r.status_code == 422:
            body = r.json()
            return ClaimResult(status='denied', reference='',
                               message=body.get('reason', 'Denied by scheme.'))
        return ClaimResult(status='malformed_response', reference='',
                           message=f'Unexpected scheme response {r.status_code} (ref {cid}).')


class UpstreamDown(Exception):
    pass
