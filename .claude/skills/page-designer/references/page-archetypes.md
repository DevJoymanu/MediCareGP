# Page Archetype Skeletons

Real class names from `static/css/main.css`. Combine with the component snippets in the `clinical-ui-polish` skill.

## 1. Dashboard

```django
{% block content %}
<div style="padding:16px;max-width:1400px;">
  <div class="stat-grid">
    <div class="stat-card">…</div> ×4
  </div>
  <div class="dash-grid">
    <div class="card"> <div class="card-header"><span class="card-title">Today's Appointments</span>
        <a class="btn-ghost" href="…">View all</a></div>
      {% for a in todays %} <div class="appt-row">…</div>
      {% empty %} <div class="empty-state">…</div> {% endfor %}
    </div>
    <div class="card">Tasks…</div>
    <div class="card">Follow-ups…</div>
  </div>
</div>
{% endblock %}
```

## 2. List page

```django
<div style="padding:16px;max-width:1400px;">
  <div class="page-header">
    <h1>Patients</h1>
    <a class="btn-primary" href="{% url 'patient_create' %}"><i class="bi bi-plus-lg"></i> New</a>
  </div>
  <form method="get" style="margin-bottom:12px;">
    <input class="crm-input" name="q" value="{{ q }}" placeholder="Name, ID number or phone…">
  </form>
  <div class="filter-pills">…status pills…</div>
  <div class="card" style="padding:0;">
    <div class="table-scroll"><table class="crm-table">…rows…</table></div>
  </div>
</div>
```

## 3. Detail page

```django
<div style="padding:16px;max-width:1000px;">
  <div class="page-header">
    <div><h1>{{ patient }}</h1></div>
    <div style="display:flex;gap:8px;">
      <a class="btn-primary" …>Primary action</a>
      <a class="btn-ghost" …>Edit</a>
      <a class="btn-ghost" …><i class="bi bi-arrow-left"></i> Back</a>
    </div>
  </div>

  {# identity card: avatar + name + facts + DANGER FLAGS first #}
  <div class="card" style="margin-bottom:14px;">
    <div style="display:flex;gap:14px;align-items:center;">
      <div class="avatar av-62 av-1">TM</div>
      <div style="flex:1;">
        <h2 class="brand-heading" style="font-size:18px;margin:0;">{{ patient }}</h2>
        <div style="font-size:13px;color:var(--text-3);">44y · Male · Momentum Health</div>
      </div>
    </div>
    {% if patient.allergies_list %}<div class="allergy-banner">…</div>{% endif %}
  </div>

  <div class="card">…section…</div>
  <div class="footer-strip">…ICD-10 chips / metadata…</div>
</div>
```

## 4. Single-screen workspace (dense)

Reference implementation: `templates/diagnosis/workspace.html`. The shape:

```
max-width:1600px
├─ context header bar (identity · flags · back link)          [sticky-ish, one row]
└─ grid: minmax(0,1fr) 400px, gap 12px
   ├─ working column: stacked .ws-card sections, collapsibles via <details>
   └─ <aside> persistent panel: position:sticky; top:68px; max-height:calc(100vh-84px)
      @media (max-width:1099px): panel → fixed bottom drawer + floating badge tab
```

Rules that made it work: explicit action buttons (no auto-compute), stale-state dimming, one accent, all states designed.

## 5. Form page

```django
<div style="padding:16px;max-width:860px;">
  <div class="card">
    <div class="card-header"><span class="card-title">{{ title }}</span></div>
    <form method="post">{% csrf_token %}
      <div class="form-grid-2">
        <div class="form-group">…label + .crm-input + .field-error…</div>
        <div class="form-group form-full">…full-width field…</div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
        <a class="btn-ghost" href="…">Cancel</a>
        <button class="btn-primary" type="submit">Save</button>
      </div>
    </form>
  </div>
</div>
```

## 6. HTML print page (standalone — no base.html)

```django
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @page { size: A4; margin: 18mm; }
  body { font: 12px/1.5 'Helvetica Neue', Arial, sans-serif; color: #111; }
  .print-hide { }  @media print { .print-hide { display:none; } }
  h1 { font-size: 17px; }  table { width:100%; border-collapse: collapse; }
  td, th { border-bottom: 1px solid #ddd; padding: 5px 8px; text-align: left; }
</style></head>
<body>
  <button class="print-hide" onclick="print()">Print</button>
  <h1>{{ practice_name }}</h1>
  …black-on-white content, no icons/badges/shadows…
</body></html>
```

reportlab PDFs: copy the structure of `_build_sick_note_pdf` (`consultations/views.py`) — SimpleDocTemplate A4, Helvetica styles, practice header, HRFlowables.

## 7. Public token page

```django
<!DOCTYPE html>… standalone, viewport meta, system font stack …
- One clear heading naming the purpose ("Check in for your appointment")
- One primary action, ≥48px tall, full-width on mobile
- Status feedback inline, big text
- Footer: practice name + phone. Nothing else.
```

Precedents: `templates/checkin/*`, `templates/results/*`, `templates/video/room.html` (patient side).
