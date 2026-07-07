# Stitch Export — Source Reference (READ-ONLY)

Provenance record for the Aetheris design language: the original Google Stitch
export ("Aetheris Clinical" / MediFlow AI) was Tailwind-based. This file
preserves its design intent and token config **for reference only** — the
working implementation is the framework-neutral CSS in `assets/aetheris.css`.
Nothing in this project may depend on Tailwind.

> Reconstructed from the export's DESIGN notes and Tailwind config values.
> If the original export files are recovered, drop them in beside this file
> verbatim; values below are the source of truth in the meantime.

## Design intent (from the export's DESIGN.md)

- Aesthetic: "sci-fi medical" — a luminous, weightless HUD over a near-white
  blue canvas. Layered translucency + backdrop blur create depth; elevation is
  expressed by MORE transparency and blur, not darker shadows.
- Ambient glow: a single electric blue (#0ea5e9) provides energy — text glow on
  hero numbers, halo on active nav, drop-glow on data lines. Everything else
  stays calm.
- Shape language: pills for anything interactive; 24px+ radii on containers;
  1px light-catching borders at 10–15% opacity on glass edges.
- Typography: Inter, light (300) at body sizes and display, opened tracking,
  generous leading; Geist at 500 for small labels with +0.05em tracking.
- Space: 8px rhythm, 24px element gaps, 32px container padding, 64px section
  gaps, 1440px max width, 12-col grid with wide gutters; whitespace and type
  shifts instead of divider lines.

## Signature CSS (as shipped by the export, Tailwind-adjacent utilities)

```css
body { background: radial-gradient(circle at top right, #e0f2ff, #f8f9ff 40%); }

.glass-panel {
  background: rgba(248, 249, 255, 0.85);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0, 101, 145, 0.1);
  box-shadow: 0 40px 60px -15px rgba(14, 165, 233, 0.08);
}
.hud-header  { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); }
.neon-glow   { text-shadow: 0 0 10px rgba(14, 165, 233, 0.4); }
.input-glow:focus {
  box-shadow: 0 0 15px rgba(14, 165, 233, 0.15);
  border-color: rgba(14, 165, 233, 0.3);
}
```

## Tailwind config (token source of truth)

```js
// tailwind.config.js — Stitch "Aetheris Clinical" export (reference only)
module.exports = {
  theme: {
    extend: {
      colors: {
        primary:                    '#006591',
        'on-primary':               '#ffffff',
        'primary-container':        '#0ea5e9',
        'inverse-primary':          '#89ceff',
        'surface-tint':             '#006591',
        secondary:                  '#4648d4',
        'secondary-container':      '#6063ee',
        tertiary:                   '#576065',
        error:                      '#ba1a1a',
        'error-container':          '#ffdad6',
        'on-error-container':       '#93000a',
        background:                 '#f8f9ff',
        surface:                    '#f8f9ff',
        'surface-container-lowest': '#ffffff',
        'surface-container-low':    '#eff4ff',
        'surface-container':        '#e5eeff',
        'surface-container-highest':'#d3e4fe',
        'on-surface':               '#0b1c30',
        'on-surface-variant':       '#3e4850',
        outline:                    '#6e7881',
        'outline-variant':          '#bec8d2',
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
        body:    ['Inter', 'sans-serif'],
        label:   ['Geist', 'sans-serif'],
      },
      fontSize: {
        'display-lg':  ['48px', { lineHeight: '1.15', fontWeight: '300' }],
        'headline-lg': ['32px', { lineHeight: '1.25', fontWeight: '400' }],
        'headline-md': ['24px', { lineHeight: '1.3',  fontWeight: '400' }],
        'body-lg':     ['18px', { lineHeight: '1.7',  fontWeight: '300' }],
        'body-md':     ['16px', { lineHeight: '1.7',  fontWeight: '300' }],
        'label-md':    ['14px', { lineHeight: '1.4',  fontWeight: '500', letterSpacing: '0.05em' }],
        'label-sm':    ['12px', { lineHeight: '1.4',  fontWeight: '500', letterSpacing: '0.05em' }],
      },
      borderRadius: {
        sm: '0.5rem', DEFAULT: '1rem', md: '1.5rem',
        lg: '2rem',   xl: '3rem',      full: '9999px',
      },
    },
  },
};
```

## Porting decisions made for this project

- Tokens became `--a-*` custom properties scoped under a root `.aetheris`
  class (opt-in per page) instead of `:root`, so the theme cannot bleed into
  default-CRM pages that use `main.css`'s own `--accent`/`--bg` variables.
- The two blues were given explicit roles: `--a-primary` (#006591, semantic)
  vs `--a-accent` (#0ea5e9, glow/data/active) — the export used
  `primary-container` for the latter, which invited misuse.
- Added what the export lacked and a clinical product requires: the
  `a-legible` high-legibility mode, `@supports` no-blur fallback,
  `prefers-reduced-transparency` / `prefers-reduced-motion` handling, a
  weight-400 floor for dense data (`.a-data`), and glow-never-carries-state.
