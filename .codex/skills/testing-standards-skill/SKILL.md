---
name: testing-standards-skill
description: Define and apply testing standards for a Django GP clinic SaaS platform. Use when writing or reviewing tests for models, services, selectors, DRF APIs, permissions, audit logging, forms, templates, billing, claims, labs, prescriptions, appointments, notifications, and deployment smoke checks.
---

# Testing Standards

## Input Expectations

- Receive the feature, bug, workflow, or module under test.
- Inspect the existing test framework and naming style.
- Identify service, API, permission, audit, and integration boundaries.

## Step-By-Step Rules

1. Test business rules at the service layer first.
2. Test selectors for important query behavior.
3. Test models for constraints, choices, and critical computed helpers.
4. Test DRF APIs for authentication, authorization, payload validation, response shape, and UUID usage.
5. Test HTML views/forms for permissions, valid submissions, invalid submissions, redirects, and rendered state.
6. Test audit event creation for medical and financial mutations.
7. Test RBAC for doctor, admin, receptionist, and patient.
8. Mock external providers for WhatsApp, email, labs, payments, and medical aid claims.
9. Add regression tests before or with bug fixes.
10. Run the narrowest meaningful test command, then broader tests when risk is high.

## Required Test Cases

- Valid workflow path.
- Invalid state transition.
- Unauthorized role.
- Wrong patient/object owner.
- Duplicate request or webhook replay where relevant.
- Missing or invalid UUID.
- Audit event presence and safe metadata.
- Provider failure handling.
- Money precision and allocation behavior for billing.

## Output Expectations

- Produce focused tests with clear fixture/factory setup.
- Use existing project test conventions.
- Keep tests deterministic and independent.
- Report exact commands run and failures found.

## Strict Coding Conventions

- Do not test implementation details when public behavior is enough.
- Do not use real external network calls in tests.
- Do not depend on test ordering.
- Do not assert against integer public identifiers.
- Do not put secrets or real patient data in fixtures.
