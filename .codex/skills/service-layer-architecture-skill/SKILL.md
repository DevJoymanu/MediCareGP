---
name: service-layer-architecture-skill
description: Implement service-layer architecture for Django GP clinic workflows. Use when adding or reviewing business logic for patient registration, appointment booking, consultations, lab requests, prescriptions, billing, medical aid claims, payments, notifications, and audit-producing actions.
---

# Service Layer Architecture

## Input Expectations

- Receive the workflow name, state change, or domain operation.
- Identify involved models, permissions, audit events, notifications, and external integrations.
- Inspect existing services/selectors before adding new ones.

## Step-By-Step Rules

1. Put mutating workflows in services.
2. Put read-heavy workflows in selectors.
3. Keep views, serializers, forms, templates, admin actions, signals, and model methods thin.
4. Use one service function for one business command.
5. Validate state transitions before mutation.
6. Use `transaction.atomic()` for multi-record changes.
7. Create audit events in the same transaction when possible.
8. Trigger external notifications through queued tasks or integration interfaces.
9. Return domain objects, DTOs, or typed results, never HTTP responses.
10. Raise domain-specific exceptions that views/APIs can translate.

## Required Workflows

- Patient registration and profile update.
- Appointment booking, rescheduling, cancellation, check-in, no-show, and completion.
- Consultation start, update, finalization, and clinical note audit.
- Lab request creation, cancellation, provider submission, and result attachment.
- Prescription issue, update, cancellation, and dispensing.
- Invoice generation, line-item update, payment allocation, claim preparation, claim submission handoff, and claim status update.
- WhatsApp/email notification scheduling and delivery status update.

## Audit Rules

- Every medical and financial service mutation must emit an audit event.
- Audit records must include actor, role, action, target, target UUID, timestamp, request metadata, and safe metadata.
- Do not include secrets or unnecessary patient details in audit metadata.

## Output Expectations

- Produce service functions/classes with clear input arguments.
- Keep services easy to test without HTTP clients.
- Add service-level tests for valid paths, invalid state transitions, authorization assumptions, audit events, and idempotency.

## Strict Coding Conventions

- Name commands with verbs.
- Keep service functions cohesive; split long workflows into private helpers only when it improves clarity.
- Do not import templates or HTTP response classes into services.
- Do not perform network calls inside database transactions unless unavoidable.
- Keep provider adapters behind integration interfaces.
