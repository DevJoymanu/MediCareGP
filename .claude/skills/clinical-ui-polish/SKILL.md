---
name: clinical-ui-polish
description: Interaction, color, motion and accessibility rules for the GP CRM's staff interface. Load this whenever touching Django templates, static/css/main.css, inline styles, buttons/badges/forms/tables, JavaScript interactions (fetch, polling, type-aheads), or anything a staff user sees — even for "small" template tweaks, new status colors, or adding a loading spinner. Also load before styling any new component so it reuses the existing token system instead of inventing new colors.
---

# Clinical UI Polish

The CRM is a **dense clinical power tool** used all day by a doctor and a receptionist. Polish here means: instantly scannable, never ambiguous about danger, zero surprises. It is NOT a component framework project — there is no Bootstrap CSS, no HTMX, no SPA. The stack is:

- One stylesheet: `medicaregp/static/css/main.css` (CSS custom properties + `crm-*`/utility classes)
- Bootstrap **Icons** only (CDN `<i class="bi bi-...">`)
- Inline styles in templates are idiomatic here for one-off layout; shared patterns get a class
- Vanilla JS + `fetch`; server JSON endpoints; HTTP polling where live data is needed (waiting room 5s, video signaling)

Work WITH these conventions. A PR that introduces a CSS framework, jQuery, or a second design language is wrong even if it looks good.

## Design tokens (already defined in main.css — reuse, never redefine)

```css
--accent: oklch(40% 0.10 260);  /* the ONE interactive accent (slate-blue) */
--accent-h: oklch(36% 0.10 260); /* hover */
--accent-rgb: 71, 85, 105;       /* for rgba() tints */
--bg: #f0f3f8;  --card-bg: #fff;  --border: #e8ecf1;
--text-1: #0d1117; --text-2: #374151; --text-3: #6b7280; --text-4: #9ca3af;
--radius: 16px; --radius-sm: 10px;
--shadow-sm / --shadow-md
```

Fonts: **DM Sans** (body/controls), **Bricolage Grotesque** (h1–h5, `.brand-heading`). Don't add font families.

## Semantic color — the hard rules

1. **Red is reserved for danger**: allergies, destructive actions, hard errors. Never use red for "high score", "busy", or emphasis. Existing precedents: `.allergy-banner`, `.tag-allergy`, `.btn-danger`, `.badge-cancelled`, the workspace `.flag-danger` chip.
2. **Never encode meaning in hue alone** — pair with fill-weight, icon, or text so it survives grayscale and color-blindness. Precedent: diagnosis likelihood bands are **High = solid fill, Medium = tonal tint, Low = outline**, all in the neutral accent, not a green→red ramp.
3. **Status palette** (already in use — match it):
   - Scheduled / info: blue family (`.badge-scheduled`, `#eff6ff`/`#1d4ed8` surfaces)
   - Completed / success: green (`.badge-completed`, `.alert-success`, `#f0fdf4`/`#15803d`)
   - Warning / review-needed / first-occurrence: amber (`#fef3c7`/`#92400e`)
   - Cancelled / danger / allergy: red (`#fee2e2`/`#991b1b`)
   - Neutral / inactive: `--text-4` + `--border` outline
4. **Role accents**: two RBAC roles exist — Doctor (full clinical) and Reception (demographics + medical aid only). Role difference is expressed by *what renders* (server-side RBAC decides), not by recoloring the UI. Don't build per-role themes.
5. **Medical-aid scheme tags**: use the neutral `.tag` / `.tag-default` shape with the scheme name as text. Schemes come and go via `SchemeConfig` — never hardcode a color per scheme name.
6. Check contrast: body text on `--card-bg` and chip text on tinted surfaces must meet WCAG AA (4.5:1; 3:1 for large/bold). The pairs above already pass — reuse them instead of picking new tints.

## Interaction polish (vanilla JS, not HTMX)

- **Disable-while-pending**: every fetch-backed button disables itself and relabels (`Run → Running…`, `Confirm provisional → Confirming…`) then restores on failure. Never leave a button clickable during a request.
- **Optimistic feedback**: after a save, show a stamp near the button (`✓ saved 14:32`, green; error text in red) that clears after ~4s — see `saveStamp` in `templates/diagnosis/workspace.html`.
- **Stale-state over silent recompute**: when inputs change after a computed result is shown, dim the result, show an "Inputs changed" chip, and pulse the re-run button. Never recompute clinical output behind the doctor's back. (Workspace differential panel is the reference implementation.)
- **Type-aheads**: debounce ~180ms, ArrowUp/Down + Enter + Escape, `mousedown` (not click) on options so blur doesn't eat the pick, close on blur with a ~120ms grace. Reuse the pattern in `workspace.html` rather than a library.
- **Polling**: 5s interval JSON polling is the house pattern for live views (waiting room). Don't introduce WebSockets — the stack is WSGI-only by decision.
- **Errors**: fetch failures get a visible message ("Network error — try again"), never a silent console log. Server 4xx JSON carries `{error: "..."}` — surface that text.

## Motion

- 150–250ms, `ease`/`ease-in-out`, on opacity/transform only. Existing: drawer slide (`.22s`), stale-panel dim, run-button pulse.
- Motion must carry meaning (state changed, attention needed). No decorative animation, no animated numbers.
- **Never animate critical clinical data** — allergy banners and red-flag content appear instantly, full opacity, no fade-in.
- Honor `prefers-reduced-motion: reduce` — gate keyframe animations behind it when adding any.

## Accessibility (hard requirement)

- Visible focus: inputs use `outline: 2px solid var(--accent); outline-offset: 1px` on focus — apply the same to custom interactive elements.
- Everything reachable by keyboard; type-aheads and the workspace already do this — match them.
- Buttons that only show an icon need `aria-label` / `title`. Chips' remove buttons: `aria-label="Remove <name>"`.
- Touch targets ≥ 44px on mobile-visible controls (bottom nav, drawer tab already comply).
- After swapping a region's content via JS, if it's an alert/result the user must notice, set `role="status"` or `aria-live="polite"` on the container.

## Component reference

For copy-paste snippets of the house components (buttons, cards, tables, badges, tags, forms, alerts, avatars, stat cards, type-ahead, empty states) read `references/components.md` in this skill.

## Anti-patterns (reject these in review)

- New hues for emphasis; red for anything but danger; meaning carried by color alone
- A second button style, new font, new radius scale, or shadow flavor
- CSS frameworks, jQuery, HTMX, WebSockets
- Spinners longer than ~300ms without text; blocking overlays for sub-second saves
- Animating allergy/red-flag content; toast-only error reporting for clinical actions
- Hiding clinical-only UI with CSS/JS instead of server-side RBAC (`medicaregp/roles.py` is the boundary — the template merely reflects it)
