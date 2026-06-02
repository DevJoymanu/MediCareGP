---
name: api-design-drf-skill
description: Build and review Django REST Framework APIs for a GP clinic SaaS platform. Use when creating serializers, viewsets, APIViews, routers, permissions, filters, pagination, API errors, webhooks, and external-facing API contracts for clinic modules.
---

# API Design With DRF

## Input Expectations

- Receive the API resource, action, or integration endpoint.
- Inspect existing router, serializer, permission, and response conventions.
- Identify the service function that owns the workflow.

## Step-By-Step Rules

1. Use DRF only for API endpoints.
2. Keep HTML views separate from API views.
3. Use UUID lookup fields for external resources.
4. Do not expose integer primary keys.
5. Keep serializers responsible for shape validation and representation.
6. Keep business rules in services.
7. Call services from `perform_create`, `perform_update`, custom actions, or APIViews.
8. Use explicit authentication and permission classes.
9. Add filtering and pagination for list endpoints.
10. Return consistent error formats.
11. Use provider-specific webhook verification before side effects.
12. Add idempotency protections for duplicate external callbacks or client retries.

## Resource Rules

- Patients API must avoid leaking clinical, billing, or identity details unless authorized.
- Appointments API must enforce doctor/receptionist/patient access rules.
- Consultations API must be doctor-restricted except safe patient-visible summaries.
- Labs API must protect requests/results and normalize provider status.
- Pharmacy API must protect prescriptions and dispensing state.
- Billing API must protect invoice, payment, and claim details by role and ownership.
- Notifications API must expose delivery state without revealing provider secrets.

## Output Expectations

- Produce serializers, views/viewsets, routers, permissions, and tests where needed.
- Use response payloads with UUIDs and stable public fields.
- Document required service calls and provider callbacks.

## Strict Coding Conventions

- Never call provider APIs directly from serializers.
- Never mutate workflow state in serializer `validate()` or `to_representation()`.
- Never trust user-supplied role, price, claim status, or provider status without service validation.
- Use `select_related` and `prefetch_related` through selectors or querysets for list performance.
- Keep API errors clear and non-leaky.
