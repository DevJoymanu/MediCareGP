---
name: django-project-structure-skill
description: Enforce production-grade Django project and app structure for a modular SaaS GP clinic platform. Use when creating, reorganizing, or reviewing Django apps, modules, URLs, settings, admin, templates, services, selectors, serializers, permissions, tasks, or migrations for patients, appointments, consultations, labs, pharmacy, billing, notifications, audit, dashboard, and accounts.
---

# Django Project Structure

## Input Expectations

- Receive the target feature, app, or module name.
- Inspect existing project conventions before adding files.
- Identify whether the work is HTML UI, DRF API, service logic, schema, async task, admin, or test work.

## Step-By-Step Rules

1. Keep Django apps modular and domain-oriented:
   - `patients`
   - `appointments`
   - `consultations`
   - `labs`
   - `pharmacy`
   - `billing`
   - `notifications`
   - `accounts`
   - `audit`
   - `dashboard`
2. Place shared cross-domain utilities in a narrow shared app only when they are genuinely reusable.
3. Keep each app independently understandable with clear module ownership.
4. Put data schema in `models.py` or `models/`.
5. Put mutating business workflows in `services.py` or `services/`.
6. Put read/query workflows in `selectors.py` or `selectors/`.
7. Put DRF serializers in `serializers.py` or `serializers/`.
8. Put HTTP orchestration in `views.py` or `views/`.
9. Put URL declarations in app-level `urls.py`.
10. Put role and object permission helpers in `permissions.py`.
11. Put async jobs in `tasks.py`.
12. Put admin registrations in `admin.py`.
13. Put forms for HTML workflows in `forms.py`.
14. Put templates under `templates/<app_name>/`.
15. Put tests under `tests/` or `tests.py` following the repository convention.

## Global Architecture Rules

- Do not put business logic in views, serializers, templates, forms, model `save()`, or signals.
- Use the service layer for appointment booking, consultation completion, lab requests, prescriptions, billing, claims, and notifications.
- Use DRF for APIs only.
- Use UUIDs for every external-facing model.
- Never expose integer primary keys in URLs, APIs, notifications, or documents intended for users.
- Add audit logging hooks for medical and financial actions.
- Enforce RBAC for doctor, admin, receptionist, and patient.
- Read secrets from environment variables only.

## Output Expectations

- Produce files in the correct app/module.
- Name modules predictably and avoid catch-all utilities.
- Include imports that do not create circular dependencies.
- Add migrations only for schema changes.
- Add focused tests when structure changes affect behavior.

## Strict Coding Conventions

- Prefer explicit service function names such as `book_appointment` and `issue_prescription`.
- Use `settings.AUTH_USER_MODEL` for user relations.
- Use `transaction.atomic()` in services that mutate multiple records.
- Keep app boundaries explicit; do not import views into services.
- Keep settings environment-driven and production-safe.
