---
name: aetheris-design-system
description: The "Aetheris Clinical" theme layer — a glassmorphic, sci-fi-medical design language (layered translucency, backdrop blur, pill shapes, ambient electric-blue glow, airy light type) extracted from a Google Stitch / MediFlow AI export and ported to framework-neutral CSS. Load this whenever building or styling UI in this project, working on templates or CSS, and ALWAYS when the user mentions Aetheris, glass/glassmorphic styling, neon/glow effects, the Stitch or MediFlow design, or asks to re-theme a page — so the correct theme (Aetheris vs the default CRM look) is chosen deliberately per surface.
---

# Aetheris Design System

A **theme layer**, not an interaction system. The `clinical-ui-polish` skill still owns motion timing, focus/keyboard behavior, loading/pending patterns, and accessibility rules — read it alongside this; nothing here overrides it. What this skill owns is the *visual language*: tokens, glass surfaces, glow, type, and component skins.

## The one decision that comes first

**A page is either Aetheris-themed or default-CRM-themed — never both.** Aetheris activates by putting `class="aetheris"` on the page's `<body>` (or a root wrapper) and linking `assets/aetheris.css`; every token and component skin is scoped under that class, so the two languages cannot bleed into each other. Applying Aetheris to a surface is a product decision (e.g. public patient pages, a re-skinned dashboard), not something to mix ad-hoc into one screen of the existing CRM. If the user hasn't said which theme a new page uses, ask — don't guess.

## The aesthetic in one paragraph

Light, airy, luminous. A near-white blue-tinted canvas (`#f8f9ff`) with a soft radial glow from the top-right corner. Content floats on **glass panels** — translucent white, 24px backdrop blur, 1px light-catching borders, and ambient cyan shadows instead of dark elevation. Interactive elements are **pills**; containers are generously rounded (24px+). Type is Inter, light-weight and open-tracked, with Geist for small labels. One vibrant **electric accent** (`#0ea5e9`) does the glowing — data highlights, active states, focus rings — while the calmer `#006591` is the semantic primary.

## Tokens (full set in `assets/aetheris.css` — the highlights)

- **Two blues, distinct jobs**: `--a-primary: #006591` = semantic primary (links, primary text accents, borders). `--a-accent: #0ea5e9` (source's `primary-container`) = the electric highlight for glows, data viz, active indicators. Don't swap them: glow is decorative, so the glowing blue must never be the only carrier of meaning.
- **Surfaces** (Material-3 ramp): `#ffffff` lowest → `#f8f9ff` background → `#eff4ff` low → `#e5eeff` container → `#d3e4fe` highest. Text: `#0b1c30` on-surface, `#3e4850` variant; outlines `#6e7881` / `#bec8d2`.
- **Secondary** `#4648d4` / container `#6063ee` (violet — sparingly, for a second data series or secondary emphasis). Tertiary `#576065`. **Error** `#ba1a1a` / container `#ffdad6` / on-container `#93000a` — error red keeps its meaning; the `clinical-ui-polish` rule stands: red only ever signals danger.
- **Type roles**: display-lg 48/300 · headline-lg 32/400 · headline-md 24/400 · body-lg 18/300 · body-md 16/300 · label-md 14/500 +0.05em · label-sm 12/500 +0.05em. Inter for display/headline/body, Geist for labels, both from Google Fonts. Tracking slightly open, line-height generous.
- **Radius**: sm .5rem · base 1rem · md 1.5rem · lg 2rem · xl 3rem · full 9999px. Buttons/chips/inputs = **full (pill)**; cards/containers = **xl**.
- **Rhythm**: 8px base unit, 24px between elements, 32px container padding, 64px between sections, 1440px max width, 12-col grid with wide gutters. Separate with whitespace and type shifts, not divider lines.

## Elevation — the signature rule

Higher layers get **more translucency and stronger blur, not darker shadows**. Shadows are ambient and tinted (`rgba(14,165,233,.08)`, huge blur, negative spread), borders are 1px at 10–15% opacity to catch light on the glass edge. If a stack of layers needs a heavy dark drop-shadow to read, the layering is wrong — flatten it.

Signature patterns (all in the stylesheet): page radial background, `.glass-panel`, `.hud-header`, `.neon-glow`, `.input-glow` focus treatment.

## Legibility beats aesthetic — the hard constraints

This is a clinical product; the glass look loses every conflict with readability:

- **Never 300-weight body text on dense clinical data** (tables, patient records, results, anything scanned under time pressure). Light weights are for display/headline sizes and marketing-ish surfaces; dense data uses 400+.
- **High-legibility mode is mandatory wiring**: add `a-legible` beside `aetheris` and the stylesheet bumps body weights 300→400, raises glass surface opacity (.85→.96), strengthens borders (~25% opacity), and drops neon text-shadows. Offer it as a user/practice setting on any Aetheris clinical surface; it's also the automatic fallback when `backdrop-filter` is unsupported and under `prefers-reduced-transparency`.
- Contrast must hold WCAG AA *through the glass*: text sits on the panel's effective (blended) background — verify against the blend, not against pure white. The bundled panel opacities were chosen so `#0b1c30` body text passes; lowering them is a contrast regression.
- Glow never carries state alone — pair active/selected with a fill or border change (the `clinical-ui-polish` "never hue alone" rule, extended to luminance).
- Motion honors `prefers-reduced-motion` — timings and rules live in `clinical-ui-polish`; this theme adds no new animation vocabulary beyond soft glow transitions.

## Components

Copy-paste recipes (buttons, chips, inputs with floating labels, cards, lists, sidebar/nav, data-viz treatment) are in `references/components.md`, all plain CSS + HTML — no Tailwind classes. The original Stitch export (design notes + Tailwind config) is preserved read-only in `references/stitch-source.md` for provenance; never make anything depend on Tailwind.

## Anti-patterns

- Glass on glass on glass — two translucent layers max above the page background; a third needs a solid (`--a-surface-lowest`) interruption or it turns to fog.
- Dark heavy shadows for elevation; opaque borders on glass; gray dividers where whitespace should separate.
- 300-weight or low-contrast text on dense data; body text below 14px.
- Neon glow on error/danger content (red stays untinted and instantly legible), or glow as the only state signal.
- Mixing Aetheris classes into default-theme pages (or vice versa) — pick the theme at the page root.
- Skipping the no-`backdrop-filter` fallback: unstyled translucency without blur reads as a rendering bug.
