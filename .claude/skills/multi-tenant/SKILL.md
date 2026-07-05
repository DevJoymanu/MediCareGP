---
name: multi-tenant
description: Tenant-isolation architecture and enforcement for turning the GP CRM into a multi-clinic product. Load this for ANY work on models, querysets/managers, migrations, authentication/RBAC, caching, background jobs, or public token endpoints once multi-tenancy is in play — and whenever the user mentions clinics, tenants, practices as separate customers, or data isolation. Cross-tenant patient-data leakage is a catastrophic failure; this skill exists to make it structurally impossible.
---

# Multi-Tenant Architecture

**Context:** the CRM is single-tenant today (one practice, Dr. Chivonivoni). This skill governs the conversion to hosting multiple independent clinics and all work thereafter. The invariant: *a user in clinic A can never read, write, count, or infer clinic B's records* — through the ORM, any view, the API, the admin, exports, or error messages.

## Isolation model

Three options, honestly costed:

| Model | Isolation | Operational cost | Fit |
|---|---|---|---|
| Shared schema, `tenant` FK on every row | Weakest — one forgotten `.filter()` leaks PHI | Lowest; keeps SQLite dev | Acceptable only with the loud-failure manager below, still the riskiest |
| **Schema-per-tenant** (django-tenants) | Strong — Postgres `search_path` scoping; a missed filter hits the wrong schema and finds nothing | Medium: Postgres required **in dev too** (SQLite cannot do schemas), per-schema migrations, backup complexity | **Recommended** |
| Database-per-tenant | Strongest | Highest: N databases to migrate/backup/monitor; connection routing | Overkill until a customer contractually demands it |

**Decision: schema-per-tenant** — for clinical data the failure mode of shared-schema (silent leakage via one unscoped query) is unacceptable, and DB-per-tenant's cost buys little over schemas. Consequences to accept explicitly:
- Local dev moves from SQLite to Postgres (docker or Railway dev DB). Update CLAUDE.md and CI when this lands.
- `migrate_schemas` replaces `migrate`; every migration runs once per tenant schema — write them idempotent and fast.
- The public React site, `/api/bookings`, and other pre-auth surfaces need tenant resolution *before* any queryset is touched.

If the user states a different model has been chosen, follow it — but apply the same enforcement layers below (they're model-independent).

## Enforcement layers (defense in depth — all of them, not one)

1. **Tenant resolution**: subdomain → tenant (`kwathema.gpcrm.app`), falling back to an explicit header for API clients. Resolution happens in middleware before auth. Unknown host = 404, never a default tenant.
2. **Request-scoped context**: middleware stores the resolved tenant in a `contextvars.ContextVar`. Nothing reads a "current tenant" global that could bleed across threads — gunicorn runs `--threads 8`.
3. **Scoped manager everywhere**: every tenant-owned model uses a base manager whose `get_queryset()` applies the tenant scope (under django-tenants the schema does this; under shared-schema it filters the FK). See `references/scaffolding.py`.
4. **Loud failure, never silent leak**: if code touches a tenant-owned model with no tenant in context (cron job, shell, misconfigured view), raise `TenantContextMissing` immediately. An exception in a background job is infinitely better than a cross-clinic query that "worked".
5. **Admin**: Django admin is either superuser-only at a non-tenant host (operations use), or tenant-scoped like everything else. Never both views of the same data.

## Tenancy × RBAC

The existing RBAC (Doctor / Reception groups, enforced in `medicaregp/roles.py` at queryset/form/view level) becomes **per-tenant membership**:

- A user belongs to a tenant and holds a role *within it* — model this as `TenantMembership(user, tenant, role)` rather than global groups, so one person can be a doctor at clinic A only.
- `is_doctor()` / `doctor_required` / `reception_patient_queryset()` gain a tenant dimension: role checks answer "what role in the *current request's* tenant", not "any group ever".
- Keep the existing pattern of enforcing at the queryset (deferred clinical columns for reception) — tenancy scopes *which rows*, RBAC scopes *which columns/views*. They compose; neither substitutes for the other.

## Public token surfaces (this repo's special case)

Check-in, results portal, and video join are **pre-auth, token-UUID** pages. The token itself must carry the tenant: resolve tenant *from the token's owning record*, verify it matches the request host's tenant, and 404 on mismatch. A token minted at clinic A used on clinic B's subdomain is an attack, not a convenience.

## Operations

- **Onboarding**: create tenant row + schema, run migrations for it, seed role groups + the diagnosis knowledge base (the seed migrations already exist — factor them to be re-runnable per schema), create the first admin membership. Script it; never hand-run.
- **Offboarding**: disable (block resolution) first; destructive deletion only after export + retention period, as clinical-records law requires. Patient data export is a legal obligation — build it before the first offboarding, not during.
- **Caching**: every cache key is prefixed with the tenant schema name. A helper, not a convention people must remember.
- **Background jobs / cron**: any job touching tenant data takes an explicit tenant argument and enters its context; "run for all tenants" iterates and enters each. Layer-4 makes forgetting this a crash, not a leak.
- **Backups**: per-schema dumps so one clinic can be restored without touching others.

## The isolation test suite (mandatory, non-negotiable)

Any tenancy work lands with tests proving isolation — template in `references/isolation_tests.py`. The shape:

- Two tenants, one user + one patient each.
- **ORM**: with tenant-A context, patient B is unreachable (count 0 / DoesNotExist) on every tenant-owned model.
- **Views/API**: user A requesting patient B's detail/JSON endpoints gets 404 (not 403 — don't confirm existence).
- **Admin**: user A's admin queryset excludes B entirely.
- **No-context**: touching a tenant-owned model with no tenant in context raises, never returns rows.
- **Tokens**: tenant-A token on tenant-B host → 404.

Treat a red isolation test like a failed allergy check: nothing ships until it's green.
