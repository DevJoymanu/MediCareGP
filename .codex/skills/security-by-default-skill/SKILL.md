---
name: security-by-default-skill
description: Apply security-by-default rules for a Django GP clinic SaaS platform. Use when implementing or reviewing authentication, authorization, RBAC, object permissions, audit logging, secure settings, secrets handling, webhooks, APIs, templates, and privacy-sensitive medical or billing workflows.
---

# Security By Default

## Input Expectations

- Receive the feature, endpoint, view, model, service, integration, or setting being changed.
- Identify actors, roles, patient ownership, object sensitivity, and audit requirements.
- Inspect current auth, permission, middleware, settings, and audit patterns.

## Step-By-Step Rules

1. Deny access by default.
2. Grant access through explicit role and object-level checks.
3. Support doctor, admin, receptionist, and patient roles.
4. Use environment variables for every secret and environment-specific setting.
5. Never hardcode credentials, tokens, API keys, SECRET_KEY, database URLs, provider secrets, or medical aid credentials.
6. Use UUID public identifiers and hide integer IDs.
7. Require authentication for all staff and patient data views.
8. Use explicit DRF authentication and permission classes for every API.
9. Verify CSRF protection for HTML mutations.
10. Verify webhooks before side effects.
11. Minimize patient and billing data in logs, notifications, and errors.
12. Create audit events for all medical and financial actions.

## RBAC Rules

- Doctors may access assigned clinical work and authorized patient clinical records.
- Receptionists may manage scheduling and permitted patient administrative data.
- Admins may manage operational records but still require explicit access to sensitive clinical data.
- Patients may access only their own permitted records, appointments, invoices, notifications, and safe summaries.
- No role may access provider secrets or internal IDs through UI or API.

## Secure Settings Rules

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, database credentials, email credentials, WhatsApp credentials, payment credentials, medical aid credentials, and lab credentials must come from environment variables.
- Production `DEBUG` must be false.
- Cookies must be secure in production.
- Logging must not expose secrets or unnecessary patient data.

## Output Expectations

- Produce permissions, decorators/mixins, secure settings, audit hooks, and security tests where relevant.
- State any required environment variables.
- State residual security assumptions clearly.

## Strict Coding Conventions

- Never bypass permission checks for convenience.
- Never rely on UI hiding as authorization.
- Never log raw request bodies for clinical, billing, webhook, or credential-bearing endpoints.
- Never include secrets in exceptions, audit metadata, or notifications.
