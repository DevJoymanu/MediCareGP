---
name: api-integrations
description: Outbound integrations for the GP CRM — medical-aid scheme gateways (eligibility, claims, remittance) on the existing medaid adapter architecture, plus email/SMS/billing providers. Load this for any work touching medicaregp/medaid/, writing or modifying an adapter, calling any external HTTP API, handling claim submission, or when the user mentions a scheme by name (CIMAS, PSMAS, First Mutual, Discovery, Momentum, Bonitas…), eligibility checks, or claim/remittance flows.
---

# API Integrations

## The data boundary — state it before writing any code

Two rules that must never be conflated:

1. **PHI never goes to third-party AI/LLM or analytics services.** No patient data in prompts to external models, no clinical text in error trackers, no analytics events carrying identifiers. (The diagnosis engine is deliberately local and rule-based for this reason.)
2. **Medical-aid scheme endpoints ARE the intended, authorized destination** for the specific member/claim data they require. Submitting a claim to CIMAS/PSMAS/First Mutual/etc. is the product working as designed. Do not "privacy-harden" claim submission into uselessness — the boundary is *what* is sent, and that is already enforced structurally:

The **ClaimBuilder** (`medaid/claim_builder.py`) is the only path from an invoice to an outbound payload. It is whitelist-only (member number, names, line items with tariff codes/amounts) and recursively rejects any payload containing `FORBIDDEN_KEYS` (subjective, assessment, allergies, medications, narrative…). Every adapter consumes ClaimBuilder output; no adapter builds its own payload from models. Extending the payload = extending the whitelist consciously, with a test.

## The architecture that already exists (extend, don't replace)

```
billing.Invoice ──ClaimBuilder──▶ sanitized payload
                                     │
SchemeConfig (admin row) ──▶ get_gateway(scheme_name)   medaid/adapters/__init__.py
                                     │  ADAPTERS registry, ManualAdapter fallback
                                     ▼
                     adapter.submit_claim(payload) → ClaimResult
```

- **Interface** (`medaid/gateway.py`): `MedicalAidGateway` with `verify_member(member_number, id_number='')`, `check_eligibility(member_number, service_date)`, `submit_claim(claim_payload)`, `get_remittance(reference)` — returning the dataclasses `MemberDetails`, `EligibilityResult`, `ClaimResult`, `RemittanceResult`. New adapters implement exactly this; calling code never changes.
- **Registration**: add the class to `ADAPTERS` in `medaid/adapters/__init__.py` and to `SchemeConfig.ADAPTER_CHOICES`; create a `SchemeConfig` row in admin. `get_gateway()` already falls back to `ManualAdapter` for unknown/unconfigured schemes — degradation is built in; preserve it.
- **Responses normalize to the dataclasses at the adapter boundary.** Scheme-specific field names, XML/JSON quirks, and status vocabularies die inside the adapter; the rest of the app speaks only the internal types.
- **Secrets**: `SchemeConfig` stores env-var **names** (`username_env`, `password_env`, `api_key_env`); `config.credentials()` resolves values from the environment at call time. Never store, log, or default actual credentials. This pattern extends to comms providers too.

A worked example adapter (HTTP, retries, taxonomy mapping) is in `references/example_adapter.py`.

## Resilience requirements for any real adapter

- **Timeouts always**: `requests` calls set `timeout=(connect, read)` — e.g. `(5, 30)`. An adapter without a timeout can hang a gunicorn worker (there is exactly 1 worker × 8 threads in prod).
- **Bounded retries with backoff** on connection errors and 5xx only — never retry a 4xx, and never retry `submit_claim` blindly (see idempotency).
- **Idempotency for claims**: send a stable idempotency key derived from the invoice (e.g. `invoice.invoice_number`) so a retry after a timeout can't double-submit; record the submission attempt *before* the call so a crash leaves evidence.
- **Circuit-breaking**: after N consecutive failures for a scheme, stop calling it for a cool-off window and degrade to the manual flow (queue via `ManualAdapter` semantics) with a clear user-facing message — a down scheme must not make reception's screen hang.
- **Graceful degradation is a feature**: everything the gateway does has a manual fallback path; keep it that way.

## Error taxonomy → user-facing states

Map every upstream response into one of these before it leaves the adapter (as `ClaimResult`/`EligibilityResult` status + message):

| Internal status | Meaning | Reception sees |
|---|---|---|
| `member_not_found` | Scheme doesn't know the number | "Member number not recognised — check the card" |
| `ineligible` | Known member, no cover for this service/date | "Not covered — collect payment directly" |
| `accepted` / `approved` | Success, reference captured | Reference number, next steps |
| `denied` | Scheme rejected the claim | Denial reason verbatim from scheme |
| `upstream_timeout` / `upstream_down` | Scheme unreachable | "Scheme not responding — queued for manual submission" |
| `malformed_response` | Scheme returned garbage | Same as above, plus an ops log |

Unknown upstream codes map to the closest bucket with the raw code preserved in the (PHI-free) log — never invent a new user-facing state per scheme.

## Observability without PHI

- Every outbound call logs: correlation ID (generate per request, echo into the scheme call where supported), scheme name, operation, HTTP status, duration, internal status. **Never** member numbers, names, or payload bodies in plaintext logs.
- Persist request/response artifacts only if encrypted-at-rest and access-controlled; default to not persisting bodies.
- The correlation ID goes back to the UI on failure ("quote ref `ab12cd` to support") so incidents are traceable without exposing data.

## Comms (email/SMS) briefly

Same rules apply: adapter-shaped client, env-var creds, timeouts, no PHI beyond the minimum the message needs (a reminder says "you have an appointment Tuesday 10:00", not the reason). Railway blocks some outbound SMTP ports — prefer HTTP APIs for email in prod.
