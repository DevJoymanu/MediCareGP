# Aetheris Component Recipes

Copy-paste HTML using the classes in `assets/aetheris.css`. Everything assumes
the page root carries `class="aetheris"` (add `a-legible` for high-legibility
mode) and the stylesheet is linked. Plain CSS — no Tailwind, works alongside
Bootstrap or the CRM's own markup unchanged.

Interaction behavior (disable-while-pending, stale states, keyboard/focus,
timing) comes from the `clinical-ui-polish` skill — these recipes are skins.

## Page scaffold

```html
<body class="aetheris">                    <!-- or "aetheris a-legible" -->
  <header class="hud-header">
    <span class="a-headline-md">Aetheris Clinical</span>
  </header>

  <main style="max-width:var(--a-max-width);margin:0 auto;padding:var(--a-pad);
               display:flex;flex-direction:column;gap:var(--a-gap);">
    <section class="glass-panel">…</section>
  </main>
</body>
```

Section spacing: `gap:var(--a-gap)` (24px) between elements, `var(--a-section-gap)`
(64px) between major sections. No `<hr>`, no border dividers — whitespace and a
`.a-label-sm` heading separate groups.

## Buttons

```html
<button class="a-btn a-btn-primary">Start consultation</button>
<button class="a-btn a-btn-ghost">Secondary action</button>
<button class="a-btn a-btn-danger">Delete record</button>   <!-- no glow, ever -->
```

Primary = electric gradient pill with hover glow + `active` scale. Ghost =
translucent glass pill. Danger = flat semantic red — deliberately outside the
glow language so it reads as danger, not decoration.

## Chips / tags

```html
<span class="a-chip">Momentum Health</span>
<span class="a-chip a-chip-active">Filtered: Today</span>   <!-- border + tint carry state; glow is garnish -->
<span class="a-chip a-chip-error">Allergy: Penicillin</span> <!-- error container colors, no glow -->
```

## Inputs (floating label)

The label floats when the input has focus **or content** — the input needs
`placeholder=" "` (single space) for the `:placeholder-shown` trick:

```html
<div class="a-field">
  <input class="a-input" id="memberNo" placeholder=" ">
  <label for="memberNo">Member number</label>
</div>
```

Selects/textareas: reuse `.a-input`, drop `border-radius` to `var(--a-radius-md)`
on textareas (a pill textarea looks wrong). Validation errors: message in
`--a-error` below the field at `label-sm` size, border-color `--a-error`.

## Cards

```html
<section class="glass-panel">
  <div class="a-label-sm" style="color:var(--a-on-surface-variant);margin-bottom:12px;">
    Today's schedule</div>
  <h2 class="a-headline-md" style="margin:0 0 16px;">9 appointments</h2>
  …content…
</section>
```

Nesting rule: content inside a glass panel sits directly on it, or on ONE more
translucent layer (`rgba(255,255,255,.5)` + small blur) — never a third.
Need another level? Use solid `var(--a-surface-lowest)` with `--a-radius-md`.

## Lists

```html
<div class="a-list">
  <a class="a-list-item" href="…">
    <span style="width:42px;height:42px;border-radius:var(--a-radius-full);
                 background:rgba(var(--a-accent-rgb),.12);display:grid;place-items:center;
                 color:var(--a-primary);font-weight:500;">TM</span>
    <span style="flex:1;">
      <span class="a-data" style="display:block;">Thabo Mokoena</span>
      <span class="a-label-sm" style="color:var(--a-on-surface-variant);">10:00 · Hypertension review</span>
    </span>
    <span class="a-chip">Checked in</span>
  </a>
</div>
```

No divider lines between rows — hover-glass (`.a-list-item:hover`) plus spacing
does the separation. Patient names and clinical values use `.a-data` (weight 400
minimum), never the 300-weight body style.

## Sidebar / nav

```html
<nav class="a-nav">
  <div class="a-headline-md neon-glow" style="padding:0 18px 24px;">Aetheris</div>
  <a class="a-nav-item active" href="…">Dashboard</a>
  <a class="a-nav-item" href="…">Patients</a>
  <a class="a-nav-item" href="…">Appointments</a>
</nav>
<main style="margin-left:260px;">…</main>
```

Active = primary tint pill + neon shadow + 1px accent border (the border keeps
state readable when glow is stripped by `a-legible`).

## Data viz

Thin vibrant lines on a quiet grid; the glow lives on the line, not the canvas:

```html
<svg viewBox="0 0 400 120">
  <line class="a-viz-grid" x1="0" y1="100" x2="400" y2="100"/>
  <polyline class="a-viz-line"  points="0,90 60,72 120,80 180,45 240,52 300,30 360,38"/>
  <polyline class="a-viz-line2" points="0,95 60,88 120,84 180,70 240,74 300,60 360,64"/>
</svg>
<div class="a-viz-value neon-glow">128<span class="a-label-sm" style="color:var(--a-on-surface-variant);"> bpm</span></div>
```

Series 1 = electric accent with drop-glow; series 2 = violet secondary, no glow.
Axis labels at `label-sm`. Numbers use tabular figures if the chart is dense:
`font-variant-numeric: tabular-nums`.

## Dense clinical tables

Glass is for the container, not the rows:

```html
<section class="glass-panel" style="padding:16px;">
  <table class="a-data" style="width:100%;border-collapse:collapse;">
    <thead><tr>
      <th class="a-label-sm" style="text-align:left;padding:10px 14px;color:var(--a-on-surface-variant);">Patient</th>
      …
    </tr></thead>
    <tbody>
      <tr style="border-radius:var(--a-radius-sm);">
        <td style="padding:12px 14px;">…</td>
      </tr>
    </tbody>
  </table>
</section>
```

Rows: weight 400, 16px size floor, hover tint `rgba(255,255,255,.6)`. If the
table is the whole page's job (results review, billing), consider `a-legible`
on that page by default.
