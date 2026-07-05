---
name: page-designer
description: Page composition and visual direction for the GP CRM — how to lay out whole screens. Load this when creating any new Django template/page, redesigning an existing screen's layout, building a dashboard/list/detail/form/workspace/print page, or designing public patient-facing pages. Companion to the clinical-ui-polish skill (which owns tokens, color, motion, components — read both when building a full page).
---

# Page Designer

This skill owns **page-level composition**: structure, hierarchy, density, responsive and print behavior. Tokens, colors, motion, and component snippets live in the `clinical-ui-polish` skill — reference it, never redefine its system.

## The product's visual direction

A clinical tool earns trust by being **calm, dense where work happens, and quiet everywhere else**:

- One accent color doing all interactive work; large neutral surfaces (`--bg` page, `--card-bg` cards).
- Typography carries hierarchy, not decoration: Bricolage Grotesque for headings, DM Sans for everything else, ~3 sizes per page (title ≈ 18px, body 13–13.5px, meta 11–12px). Tabular numerals / `ui-monospace` for ICD-10 codes, scores, times, money.
- Whitespace groups; borders separate only when whitespace can't. 4/8px spacing grid.
- Every screen answers in one glance: *who is this about, what needs attention, what's my next action.* Patient identity + danger flags (allergies) always outrank everything else on clinical pages.
- Avoid template-default genericism: no hero sections, no centered marketing layouts in the app, no icon soup. Density is a feature for staff; generosity is for public patients.

## Page scaffolding (authenticated app)

Every staff page extends `base.html`, which provides sidebar + topbar + `main-content`. Fill these blocks:

```django
{% extends 'base.html' %}
{% block title %}Page — GP CRM{% endblock %}
{% block page_title %}Page Title{% endblock %}      {# topbar heading #}
{% block page_sub %}context line{% endblock %}       {# topbar subline — use for patient/date context #}
{% block extra_head %}<style>/* page-scoped CSS */</style>{% endblock %}
{% block content %} … {% endblock %}
{% block extra_scripts %}<script>…</script>{% endblock %}
```

Content area conventions:
- Wrap in a padded container: `style="padding:16px;max-width:<archetype width>;"`.
- Width by archetype: forms/detail ≈ 860–1000px · lists/dashboards fluid with `max-width:1400px` · dense workspaces up to 1600px with a grid.
- In-page header when actions belong to the page: `.page-header` with title left, `.btn-primary`/`.btn-ghost` actions right.
- Breadcrumb need is rare — the sidebar + `page_sub` cover orientation. If a page is 2+ levels deep (e.g. consultation under a patient), put the parent link as a `btn-ghost` "← Back to …" in the header actions instead of a breadcrumb bar.

## Archetypes

Skeletons with real class names are in `references/page-archetypes.md`. Pick the archetype first; deviating from all of them is a design decision to state explicitly.

1. **Dashboard** — `.stat-grid` up top, then `.dash-grid` of cards (today's list, tasks, follow-ups). Every card has an action link and an empty state.
2. **List** — search input (GET `q`) + `.filter-pills` + `.table-scroll > .crm-table` (or card rows on touch-heavy screens) + `.empty-state`. Row click → detail.
3. **Detail** — identity header card (avatar, name, key facts, danger flags), then sectioned cards, then a `.footer-strip` for codes/metadata. Actions in the page header.
4. **Single-screen workspace** — the dense power-tool pattern: sticky context header, center working column, persistent right panel (sticky ≤ desktop, bottom drawer with badge-tab under ~1100px). Reference implementation: `templates/diagnosis/workspace.html`.
5. **Form page** — one card, `.form-grid-2/3`, labels above inputs, `.field-error` inline, submit row right-aligned (`btn-primary` + `btn-ghost` cancel). Long forms: group with uppercase section labels, never wizards.
6. **Print/PDF** — two mechanisms, choose deliberately:
   - *HTML print page* (referral forms, full-record printouts): standalone template, no `base.html`, `@media print` CSS, A4-safe margins, black-on-white, `print-hide` class for buttons. Precedent: `patient_print_all.html`.
   - *reportlab PDF* (documents that leave the practice, e.g. sick note): build in the view; precedent `_build_sick_note_pdf` in `consultations/views.py`. Match its Helvetica + practice-header look.
7. **Public token page** (check-in, results portal, video join): standalone minimal template — patients never see the CRM shell. Big text, one action, ≥44px targets, works on a cheap phone. No login, token in URL, nothing sensitive beyond the page's purpose.

## Responsive rules

- Base shell handles sidebar collapse + mobile `.bottom-nav`; don't reinvent.
- Design desktop-first, then check: grids collapse to one column (the `form-grid-*` and `dash-grid` classes already do); side panels become drawers, not squished columns; tables stay in `.table-scroll`.
- Test at ~1280 (desktop), ~810 (tablet), ~390 (phone) before calling a page done.

## States are part of the page

A page isn't designed until **empty, loading, error** are: empty states with a next action (see `clinical-ui-polish` reference), fetch regions with disable-while-pending + inline error text, and long lists with a sensible default sort noted in the header. Never ship a page where an empty queryset renders as a blank card.
