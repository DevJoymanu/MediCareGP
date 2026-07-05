---
name: research
description: Investigation method for the GP CRM — turn technical/domain questions into decisions, not summaries. Load this whenever the user asks to research, investigate, evaluate, compare, or choose between libraries/approaches/standards, asks "what's the best way to…", "should we use X or Y", mentions writing an ADR, or raises domain questions (medical coding standards, medical-aid claim formats, health-data regulation, hosting options).
---

# Research → Decision

Research for this project succeeds when it ends in a **decision the repo can act on**, recorded where the next session will find it. A pile of findings with no recommendation is a failed run.

## Guardrail first

Never send patient data, credentials, or revealing internal specifics to external services while researching. Queries stay generic: "Django schema-per-tenant migration performance" — never a real patient detail, a member number, or a proprietary claim-format sample. If a vendor form demands specifics to answer, flag it to the user instead of submitting.

## Method

1. **Frame before searching.** Write down: the question in one sentence; what a *good enough* answer looks like (success criteria); what decision this feeds; the deadline reality (an hour's research for a reversible choice, deeper for one-way doors like the tenancy model).

2. **Gather from primary sources.** Official docs, release notes, PEPs/DEPs, spec bodies, the library's own issue tracker — before blog posts. Capture a citation (URL + accessed date) for every load-bearing claim. Note recency explicitly: Django-ecosystem answers rot fast, and this repo pins Django 4.2 / Python 3.9 — a feature in Django 5.x is not an answer.

3. **Separate fact from inference.** In notes and output, mark what a source states vs what you're concluding. Flag uncertainty honestly ("maintainer activity unclear; last release 14 months ago") — a confident wrong recommendation is the worst outcome.

4. **Compare against explicit criteria** — always including this project's fixed constraints:
   - Fits the stack: Django 4.2 / Python 3.9, WSGI-only (no Channels/ASGI), SQLite-dev/Postgres-prod, vanilla-JS templates, Railway single service.
   - Privacy: no PHI to third-party AI/analytics; scheme endpoints are the authorized exception.
   - RBAC/isolation impact: does it respect or complicate the Doctor/Reception boundary and (future) tenancy?
   - Cost: Railway resource ceiling, licensing, per-call pricing.
   - Maintenance: bus factor, release cadence, migration burden, what it does to `requirements.txt`.
   A comparison table with these rows beats prose.

5. **Decide and record.** Output an ADR using `references/adr-template.md`, saved to `docs/adr/NNNN-short-slug.md` (create `docs/adr/` on first use; number sequentially). If the user maintains the Notion GP CRM hub, offer to mirror it there — the repo copy is canonical.

## Output contract

Every research run ends with, in this order:
1. **Recommendation** in one or two sentences (first — the user asked for a decision).
2. The ADR file written to `docs/adr/`.
3. Open questions / risks that could reverse the decision, each with what evidence would settle it.

Existing decisions have inertia: check `CLAUDE.md` and `docs/adr/` before recommending a change to something already decided (e.g. "no WebSockets", "payments removed by choice", "committed React build"). Overturning a recorded decision requires addressing *why it was made*, not just the merits of the alternative.

## Checklist (run before writing the ADR)

- [ ] Question + success criteria written before searching
- [ ] ≥2 independent primary sources for the load-bearing claims, cited with dates
- [ ] Compatibility verified against Django 4.2 / Python 3.9 / WSGI specifically
- [ ] Facts and inferences distinguished; uncertainties flagged
- [ ] Options compared against the fixed criteria, not vibes
- [ ] A recommendation exists and its consequences (including costs) are stated
- [ ] Nothing sensitive left in any external query history
