---
name: cicd-pipeline
description: CI/CD for the GP CRM — GitHub Actions pipeline, Railway deploy behavior, migration safety for a live clinical database, and the deploy-failure runbook. Load this when adding or editing anything under .github/workflows, changing railway.json or deploy config, adding test tooling, debugging "my change isn't deploying", planning a risky migration, or setting up lint/security checks.
---

# CI/CD Pipeline

## Current reality (don't assume more exists)

- **No CI is configured yet** — there is no `.github/workflows/`. The test suite (80 Django `TestCase` tests) runs locally via `python manage.py test` from `medicaregp/`.
- **Railway auto-deploys `main` only.** There is no deploy step to write; CI's job is to gate what reaches `main`. Work happens on feature branches; merging to `main` IS the deploy trigger.
- `railway.json` runs gunicorn with `--bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120` (hardcoded port, not `$PORT` — known quirk, works because Railway maps it).
- **Migrations are NOT auto-run on deploy.** After merging a migration, run `railway run python manage.py migrate` (or add it as a pre-deploy command deliberately).
- No linters/pytest in `requirements.txt`. The Django test runner is the house runner — don't convert the suite to pytest as a side effect of adding CI.

## The pipeline to install

A ready-to-use workflow is bundled at `assets/ci.yml` — copy it to `.github/workflows/ci.yml`. Stages and why:

1. **Install** — Python 3.9 (match prod), `pip install -r requirements.txt`, cache pip.
2. **Django system check** — `python manage.py check` catches broken settings/urls cheaply.
3. **Missing-migrations gate** — `python manage.py makemigrations --check --dry-run`. A model change without its migration deploys as a time bomb; fail fast here.
4. **Tests against Postgres** — a `postgres:15` service container with `DATABASE_URL` set, because prod is Postgres while local dev is SQLite; this is where dialect drift (JSONField lookups, case sensitivity, constraint behavior) gets caught. The full suite is the regression/golden gate — keep it green, keep it growing with every feature (the project's convention: every feature lands with tests).
5. **Security audit** — `pip-audit` on requirements. Start as `continue-on-error: true`, tighten once the baseline is clean.
6. **Lint (optional, additive)** — if introducing `ruff`, add it as a separate job that starts advisory; don't reformat the codebase in the same PR that adds CI.

Gotcha the tests depend on: new Django apps must be added to the alias tuple in `medicaregp/medicaregp/__init__.py` and `tests.py` files must use absolute imports — otherwise test discovery breaks with import errors that look like CI infrastructure failures.

## Secrets & PHI discipline

- Secrets live in GitHub Actions secrets and Railway variables only. The codebase pattern to preserve: `medaid.SchemeConfig` stores **env-var names**, never credential values — resolution happens at call time from the environment.
- Never `echo`/print env in workflows; never commit `.env`. If a step needs to debug config, print variable *names*, not values.
- Log hygiene: patient data must never appear in CI logs. Test fixtures are synthetic; keep it that way — a test that pastes a real patient record into an assertion is a data leak into GitHub's log retention.

## Migration safety on a live clinical DB

The production database holds patient records; treat every migration as running against irreplaceable data.

- **Additive first**: add nullable column → deploy → backfill (data migration or command) → tighten constraints in a later release. Never drop/rename a column in the same release that stops writing it (gunicorn restarts are not atomic with migrate).
- **No destructive ops** (`RemoveField`, `DeleteModel`, table truncation) without: a stated plan, a `pg_dump` taken first (`railway run pg_dump $DATABASE_URL > backup.sql`), and confirmation the data is genuinely dead.
- Respect the codebase's immutability invariants: `TariffRate` is append-only (billing history), `DifferentialResult` snapshots are frozen (medico-legal). A migration that rewrites those rows is a bug even if it "cleans up".
- Data migrations must be idempotent (`get_or_create`, `update` filtered precisely) — Railway may retry a failed deploy.

## Railway operational knowledge (hard-won)

- **"Nothing is deploying"** → check that `main` actually moved (`git log origin/main`). Feature branches never deploy.
- **Build queue pile-ups**: rapid pushes to `main` queue builds; wait for the current one or cancel stale builds in the dashboard rather than pushing again.
- **Builder config errors** (Railpack/`mise.toml`-style failures): pin the builder in `railway.json` (currently nixpacks) rather than letting auto-detection drift.
- **SMTP**: Railway blocks common outbound SMTP ports on some plans — if email sending times out in prod but works locally, that's the first suspect; use an HTTP email API or the provider's alternate port.
- **Rollback** = `git revert <bad-commit> && git push origin main` (Railway redeploys). For data damage, restore from the pre-migration dump. Practice this before needing it.
- Static files are collected at build; the public React site is pre-built and **committed** (`medicaregp/static/website/`) so the Python-only build needs no Node step — don't "optimize" that away.

## Failure runbook

| Symptom | First move |
|---|---|
| CI red on `makemigrations --check` | You changed a model without a migration — `python manage.py makemigrations <app>` and commit it |
| Tests pass locally (SQLite), fail in CI (Postgres) | Dialect drift — reproduce with a local Postgres (`DATABASE_URL=…`), fix the query, not the test |
| Import errors only during test discovery | New app missing from the alias tuple in `medicaregp/medicaregp/__init__.py`, or a relative import in a `tests.py` |
| Deploy green but site 502s | Check Railway logs: usually missing env var or migration not run (`railway run python manage.py migrate`) |
| Deploy green, feature absent | You merged to a branch, not `main` |
| pip-audit newly red | A dep got a CVE — bump the pin in `requirements.txt`; if no fix exists, document the accepted risk in the PR |
