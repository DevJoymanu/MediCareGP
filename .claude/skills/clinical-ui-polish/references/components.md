# GP CRM Component Reference

Copy-paste snippets using the classes that already exist in `medicaregp/static/css/main.css`. Inline styles are fine for one-off spacing; promote to a class once a pattern repeats.

## Buttons

```html
<a href="…" class="btn-primary"><i class="bi bi-plus-lg"></i> New Patient</a>
<a href="…" class="btn-ghost"><i class="bi bi-printer"></i> Print</a>
<button type="submit" class="btn-danger"><i class="bi bi-trash"></i> Delete</button>
```

Disable-while-pending (fetch actions):

```js
btn.disabled = true; btn.textContent = 'Saving…';
post(url, payload).then(({ok, data}) => {
  btn.disabled = false; btn.textContent = 'Save';
  stamp.textContent = ok ? '✓ saved ' + data.saved_at : (data.error || 'save failed');
  stamp.style.color = ok ? '#15803d' : '#b91c1c';
  setTimeout(() => stamp.textContent = '', 4000);
});
```

## Cards

```html
<div class="card" style="margin-bottom:14px;padding:16px 20px;">
  <div class="card-header">
    <div>
      <div class="card-title">Section title</div>
      <div class="card-sub">supporting line</div>
    </div>
  </div>
  …content…
</div>
```

Compact label style used inside dense cards (workspace):

```html
<div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-3);margin-bottom:8px;">Label</div>
```

## Tables

Always wrap in `.table-scroll` so wide tables scroll instead of breaking layout:

```html
<div class="table-scroll">
  <table class="crm-table">
    <thead><tr><th>Patient</th><th>Date</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>…</td><td>…</td><td><span class="badge badge-scheduled">Scheduled</span></td></tr>
    </tbody>
  </table>
</div>
```

## Badges & tags

```html
<span class="badge badge-scheduled">Scheduled</span>
<span class="badge badge-completed">Completed</span>
<span class="badge badge-cancelled">Cancelled</span>
<span class="badge badge-noshow">No-Show</span>
<span class="badge badge-walkin">Walk-In</span>

<span class="tag tag-allergy">Penicillin</span>     <!-- red — allergies ONLY -->
<span class="tag tag-chronic">Hypertension</span>
<span class="tag tag-default">Momentum Health</span> <!-- scheme names: neutral -->
```

Likelihood/confidence chips (weight, not hue — from the diagnosis workspace):

```html
<span class="band band-high">HIGH</span>   <!-- solid var(--accent), white text -->
<span class="band band-med">MED</span>     <!-- rgba(var(--accent-rgb), .14) tint -->
<span class="band band-low">LOW</span>     <!-- outline only, --text-4 -->
```

## Alerts / messages

```html
<div class="alert alert-success"><i class="bi bi-check-circle"></i> Saved.</div>
<div class="alert alert-error"><i class="bi bi-exclamation-circle"></i> Something failed.</div>
<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> Review needed.</div>
<div class="alert alert-info"><i class="bi bi-info-circle"></i> FYI.</div>
```

Allergy banner (clinical danger — instant, never animated):

```html
<div class="allergy-banner"><i class="bi bi-exclamation-octagon"></i>
  Allergies: {{ patient.allergies_list|join:", " }}</div>
```

## Forms

```html
<div class="form-grid-2">           <!-- or form-grid-3 / .form-full for spans -->
  <div class="form-group">
    <label>First name</label>
    <input type="text" name="first_name" class="crm-input">
    {% if form.first_name.errors %}<div class="field-error">{{ form.first_name.errors.0 }}</div>{% endif %}
  </div>
  <div class="form-group">
    <label>Gender</label>
    <select name="gender" class="crm-select">…</select>
  </div>
</div>
```

## Avatars

```html
<div class="avatar av-36 av-1">{{ p.first_name|first|upper }}{{ p.last_name|first|upper }}</div>
<!-- sizes: av-36 / av-40 / av-44 / av-62 · color variants av-1 … av-8 -->
```

## Stat cards (dashboard)

```html
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-icon"><i class="bi bi-people"></i></div>
    <div class="stat-number">128</div>
    <div class="stat-label">Patients</div>
    <div class="stat-sub">+4 this week</div>
  </div>
</div>
```

## Empty state

Every list/panel needs one — never render a blank region:

```html
<div class="empty-state">
  <i class="bi bi-clipboard2-pulse"></i>
  <p>No consultations yet. <a href="{% url 'consultation_create' %}">Start one</a>.</p>
</div>
```

## Type-ahead (vanilla JS house pattern)

Markup: a `.ta-wrap` positioned parent, an input, and a `.ta-drop` list of `.ta-item`s.
Behavior contract: debounce 180ms · ArrowUp/Down moves `.active` · Enter picks · Escape closes · options use `mousedown` + `preventDefault` (so input blur doesn't swallow the click) · blur closes after ~120ms.
Reference implementation: `attachTypeahead()` and the patient-selector module in `medicaregp/templates/diagnosis/workspace.html`. Copy that; don't add a library.

## Filter pills (list pages)

```html
<div class="filter-pills">
  <a class="filter-pill {% if not status %}active{% endif %}" href="?">All</a>
  <a class="filter-pill {% if status == 'Scheduled' %}active{% endif %}" href="?status=Scheduled">Scheduled</a>
</div>
```
