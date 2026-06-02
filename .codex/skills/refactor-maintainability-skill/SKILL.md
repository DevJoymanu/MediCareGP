---
name: refactor-maintainability-skill
description: Refactor Django GP clinic platform code for maintainability without changing behavior. Use when reducing duplication, moving business logic out of views/serializers/templates, improving service-layer boundaries, simplifying queries, clarifying names, extracting helpers, and reviewing code quality.
---

# Refactor Maintainability

## Input Expectations

- Receive the module, feature, smell, or code quality issue.
- Inspect current behavior and tests before changing code.
- Identify whether the change is behavior-preserving or requires a feature owner.

## Step-By-Step Rules

1. Preserve existing product behavior.
2. Keep the refactor scope narrow.
3. Move business logic from views, serializers, templates, model save methods, and signals into services.
4. Move read-heavy query composition into selectors.
5. Remove duplication only when the shared concept is real.
6. Improve names when they clarify domain meaning.
7. Replace broad utility modules with domain-specific helpers.
8. Avoid unrelated formatting churn.
9. Maintain UUID public identifier behavior.
10. Maintain audit logging behavior.
11. Maintain RBAC and object permissions.
12. Run focused tests after the refactor.

## Refactor Targets

- Long views that perform workflow mutations.
- Serializers that create invoices, claims, prescriptions, lab requests, or appointment state changes.
- Templates with hidden business decisions.
- Models with workflow side effects in `save()`.
- Repeated permission checks that need a named permission helper.
- Repeated query patterns that need selectors.
- Provider-specific code mixed into business services.

## Output Expectations

- Produce small, reviewable diffs.
- State what behavior was preserved.
- State what tests were run.
- Leave handoff notes for feature, security, deployment, or QA work outside the refactor scope.

## Strict Coding Conventions

- Do not change URLs, API payloads, database schema, permissions, or workflow states unless explicitly requested.
- Do not remove audit events.
- Do not introduce new dependencies without clear need.
- Do not create abstract frameworks for one-off duplication.
- Do not hide errors by broad exception handling.
