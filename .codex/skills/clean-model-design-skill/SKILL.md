---
name: clean-model-design-skill
description: Design clean Django models for a GP clinic SaaS platform. Use when creating or reviewing model fields, relationships, constraints, UUID public identifiers, medical audit fields, billing entities, appointments, patients, consultations, labs, prescriptions, claims, payments, and migrations.
---

# Clean Model Design

## Input Expectations

- Receive the domain entity or schema change.
- Inspect existing model conventions, base models, managers, and migrations.
- Identify external-facing references and audit-sensitive actions.

## Step-By-Step Rules

1. Model only durable data and invariants.
2. Keep workflow behavior out of model methods except simple invariant helpers.
3. Add a UUID public identifier to every external-facing model.
4. Keep internal primary keys private.
5. Use explicit `related_name` values.
6. Use `settings.AUTH_USER_MODEL` for user links.
7. Add timestamps for created and updated records.
8. Add created-by/updated-by fields when ownership or accountability matters.
9. Use database constraints for uniqueness, valid choices, and integrity.
10. Use indexes for common lookup fields such as UUIDs, patient, doctor, appointment date, status, invoice status, and claim reference.
11. Use clear status fields for workflows with constrained state transitions.
12. Create migrations with minimal, reversible changes.

## GP Clinic Model Rules

- `patients` owns demographics, contact details, identifiers, and patient status.
- `appointments` owns booking slots, doctor assignment, status, and attendance state.
- `consultations` owns encounter records, notes metadata, diagnoses summary references, and clinical workflow state.
- `labs` owns lab requests, requested tests, result metadata, and provider references.
- `pharmacy` owns prescriptions, prescription items, dispensing state, and medicine references.
- `billing` owns invoices, line items, payments, medical aid claim records, claim statuses, and allocation records.
- `notifications` owns message intents, delivery attempts, provider IDs, and delivery state.
- `audit` owns immutable action records for medical and financial events.

## Audit Requirements

- Audit patient demographic updates.
- Audit appointment status changes.
- Audit consultation note creation and updates.
- Audit lab request creation, cancellation, and result attachment.
- Audit prescription creation, update, cancellation, and dispensing.
- Audit invoice, payment, and claim lifecycle changes.
- Store actor, role, action, target model, target UUID, timestamp, request metadata, and safe change metadata.

## Output Expectations

- Produce model definitions with clear fields, choices, constraints, and indexes.
- Produce migrations and describe ordering dependencies.
- Keep migrations scoped to the requested schema change.

## Strict Coding Conventions

- Use `uuid.uuid4` defaults for UUID fields.
- Use `TextChoices` for workflow states.
- Use decimal fields for money, never floats.
- Use timezone-aware date/time fields.
- Do not override `save()` for workflow side effects.
- Do not store secrets, raw provider credentials, or unnecessary patient data.
