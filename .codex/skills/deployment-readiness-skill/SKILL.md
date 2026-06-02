---
name: deployment-readiness-skill
description: Prepare and review deployment readiness for a Django GP clinic SaaS platform. Use when working on Procfile, Docker, settings, environment variables, static/media files, database configuration, migrations, health checks, workers, schedulers, logging, CI/CD, and production release commands.
---

# Deployment Readiness

## Input Expectations

- Receive the deployment target, runtime issue, settings change, or release requirement.
- Inspect existing settings, Procfile, WSGI/ASGI, static/media setup, database config, and task workers.
- Identify required environment variables.

## Step-By-Step Rules

1. Keep deployment configuration separate from product behavior.
2. Read secrets and environment-specific values from environment variables.
3. Require production `DEBUG=false`.
4. Make `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` environment-driven.
5. Configure database from environment variables.
6. Configure static file collection and serving strategy.
7. Configure media storage explicitly.
8. Include release commands for migrations and collectstatic.
9. Include worker/scheduler processes for notifications, claims, lab polling, and retries when async tasks exist.
10. Add health/readiness checks for hosting platforms.
11. Keep logs useful but free of secrets and unnecessary patient data.
12. Add CI/CD checks for tests, migrations, linting, and deployment smoke checks where appropriate.

## Environment Variable Rules

- Require `SECRET_KEY`.
- Require `DEBUG`.
- Require `ALLOWED_HOSTS`.
- Require `CSRF_TRUSTED_ORIGINS`.
- Require database connection settings.
- Require email, WhatsApp, payment, lab, and medical aid credentials only when those providers are enabled.
- Never provide real credentials in committed files.

## Output Expectations

- Produce deployment files only when needed.
- Document startup, release, worker, and smoke-test commands.
- Preserve local development behavior while making production behavior explicit.

## Strict Coding Conventions

- Do not hardcode hostnames, credentials, or provider secrets.
- Do not disable security middleware for deployment convenience.
- Do not run migrations from application import time.
- Do not log raw patient records, payment payloads, webhook bodies, or secrets.
