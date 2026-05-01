# CrashWeb UI Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace navy/blue custom UI with GitHub-style near-monochrome slate developer tool aesthetic, rebrand to CrashWeb, rename nav items throughout — CSS-only, no Python changes.

**Architecture:** Full rewrite of `base.html` inline styles + targeted per-template edits. All Jinja logic untouched. No new dependencies. Docker image rebuild is the dev loop: edit → `docker compose build flask-web && docker compose up -d flask-web` → refresh browser.

**Tech Stack:** Flask/Jinja2 templates, inline CSS, inline SVG icons (Feather icon set shapes)

---

### Task 1: Rewrite base.html — CSS + nav

**Files:**
- Modify: `web/templates/base.html`

- [ ] **Step 1: Replace entire base.html**

```bash
cat > /home/sbera/git/personal/crashweb/web/templates/base.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CrashWeb{% endblock %}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; background: #f6f8fa; color: #1f2328; font-size: 14px; }

        /* --- Nav --- */
        nav { background: #24292f; padding: 0 24px; display: flex; align-items: center; gap: 0; }
        nav a.brand { color: #fff; font-weight: 600; font-size: 15px; padding: 12px 20px 12px 0; margin-right: 4px; text-decoration: none; display: flex; align-items: center; gap: 8px; }
        nav a.brand:hover { color: #fff; text-decoration: none; }
        nav a.nav-link { color: rgba(255,255,255,0.7); text-decoration: none; font-weight: 500; padding: 6px 12px; border-radius: 6px; transition: color 0.1s, background 0.1s; }
        nav a.nav-link:hover { color: #fff; text-decoration: none; background: rgba(255,255,255,0.06); }
        nav a.nav-link.active { color: #fff; background: #373e47; }

        /* --- Layout --- */
        .container { margin: 20px auto; padding: 0 24px; }

        /* --- Breadcrumb --- */
        .breadcrumb { margin-bottom: 16px; font-size: 13px; color: #656d76; }
        .breadcrumb a { color: #0969da; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }

        /* --- Cards --- */
        .card { background: #fff; border-radius: 6px; border: 1px solid #d0d7de; padding: 20px; margin-bottom: 20px; }
        .card > h2 { font-size: 16px; color: #1f2328; border-bottom: 1px solid #d0d7de; padding-bottom: 12px; margin-bottom: 16px; }
        h1 { font-size: 22px; margin-bottom: 16px; }

        /* --- Tables --- */
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #d0d7de; }
        th { background: #f6f8fa; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #656d76; position: sticky; top: 0; white-space: nowrap; }
        tbody tr:last-child td { border-bottom: none; }
        tbody tr:hover { background: #f6f8fa; }
        .table-wrapper { overflow-x: auto; max-height: 70vh; overflow-y: auto; }

        /* --- Links --- */
        a { color: #0969da; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* --- Inputs --- */
        textarea { width: 100%; min-height: 100px; padding: 12px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; border: 1px solid #d0d7de; border-radius: 6px; resize: vertical; background: #fff; }
        textarea:focus { outline: 2px solid #0969da; outline-offset: 0; }
        input[type="text"], select { padding: 6px 10px; border: 1px solid #d0d7de; border-radius: 6px; font-size: 13px; background: #fff; }
        input[type="text"]:focus, select:focus { outline: 2px solid #0969da; outline-offset: 0; }

        /* --- Buttons --- */
        button, .btn { background: #1f2328; color: #fff; border: 1px solid rgba(0,0,0,0.15); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; display: inline-block; text-decoration: none; }
        button:hover, .btn:hover { background: #32383f; text-decoration: none; }
        .btn-sm { padding: 4px 10px; font-size: 12px; }
        .btn-ghost { background: #f6f8fa; color: #1f2328; border: 1px solid #d0d7de; }
        .btn-ghost:hover { background: #eaeef2; }
        .btn-danger { background: #dc3545; border-color: transparent; color: #fff; }
        .btn-danger:hover { background: #b02a37; }

        /* --- Error --- */
        .error { background: #ffebe9; border: 1px solid #ff818266; color: #82071e; padding: 12px; border-radius: 6px; margin-bottom: 16px; }

        /* --- Pagination --- */
        .pagination { margin-top: 16px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
        .pagination a, .pagination span { padding: 5px 10px; border: 1px solid #d0d7de; border-radius: 6px; text-decoration: none; color: #1f2328; font-size: 13px; }
        .pagination a:hover { background: #f6f8fa; text-decoration: none; }
        .pagination .active { background: #0969da; color: #fff; border-color: #0969da; }

        /* --- Meta --- */
        .meta { color: #656d76; font-size: 13px; margin-bottom: 12px; }

        /* --- Truncate --- */
        td.truncate { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        td.truncate:hover { white-space: normal; word-break: break-all; }

        /* --- Stat cards --- */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .stat-card { background: #fff; border-radius: 6px; border: 1px solid #d0d7de; padding: 20px; text-align: center; cursor: pointer; transition: background 0.1s, border-color 0.1s; }
        .stat-card:hover { background: #f6f8fa; border-color: #57606a; text-decoration: none; }
        .stat-card .stat-icon { color: #656d76; margin-bottom: 8px; display: flex; justify-content: center; }
        .stat-card .number { font-size: 32px; font-weight: 700; color: #1f2328; }
        .stat-card .label { font-size: 13px; color: #656d76; margin-top: 4px; }

        /* --- Filters --- */
        .filters { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }
        .filters label { font-size: 12px; font-weight: 600; color: #656d76; display: block; margin-bottom: 3px; }

        /* --- Signal badges (semantic — unchanged) --- */
        .signal-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; background: #dfe6e9; color: #555; }
        .signal-4  { background: #fab1a0; color: #721c24; }
        .signal-6  { background: #ffeaa7; color: #856404; }
        .signal-7  { background: #fab1a0; color: #721c24; }
        .signal-8  { background: #fab1a0; color: #721c24; }
        .signal-11 { background: #fab1a0; color: #721c24; }
        .signal-24 { background: #fdcb6e; color: #856404; }
        .signal-25 { background: #fdcb6e; color: #856404; }
        .signal-31 { background: #fab1a0; color: #721c24; }

        /* --- Pre/Code --- */
        .pre-wrap { position: relative; }
        .pre-wrap .copy-btn { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.08); color: #e6edf3; border: 1px solid rgba(255,255,255,0.15); padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; opacity: 0.85; transition: opacity 0.15s, background 0.15s; }
        .pre-wrap .copy-btn:hover { opacity: 1; background: rgba(255,255,255,0.15); }
        .pre-wrap .copy-btn.copied { background: #238636; border-color: #238636; color: #fff; opacity: 1; }
        pre { background: #161b22; color: #e6edf3; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.5; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }
        pre .line-no { color: #656d76; user-select: none; display: inline-block; width: 40px; text-align: right; margin-right: 16px; }

        /* --- Tabs --- */
        .tabs { display: flex; border-bottom: 1px solid #d0d7de; margin-bottom: 16px; }
        .tab { padding: 8px 16px; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; font-weight: 500; color: #656d76; }
        .tab.active { color: #1f2328; border-bottom-color: #0969da; }
        .tab:hover { color: #1f2328; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* --- Detail grid --- */
        .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .detail-grid .field-label { font-size: 11px; font-weight: 600; color: #656d76; text-transform: uppercase; letter-spacing: 0.5px; }
        .detail-grid .field-value { font-size: 14px; margin-top: 2px; }

        /* --- Badges (semantic — unchanged) --- */
        .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
        .badge + .badge { margin-left: 4px; }
    </style>
</head>
<body>
    <nav>
        <a class="brand" href="{{ url_for('index') }}">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            CrashWeb
        </a>
        <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">Dashboard</a>
        <a class="nav-link {% if request.endpoint in ('cores', 'core_detail') %}active{% endif %}" href="{{ url_for('cores') }}">Cores</a>
        <a class="nav-link {% if request.endpoint in ('devices', 'device_detail') %}active{% endif %}" href="{{ url_for('devices') }}">Devices</a>
        <a class="nav-link {% if request.endpoint == 'revisions' %}active{% endif %}" href="{{ url_for('revisions') }}">Revisions</a>
        <a class="nav-link {% if request.endpoint == 'analyze' %}active{% endif %}" href="{{ url_for('analyze') }}">Analysis</a>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    {% block scripts %}{% endblock %}
</body>
</html>
HTMLEOF
```

- [ ] **Step 2: Build and start flask-web**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

- [ ] **Step 3: Verify nav and base styles**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
```
Expected: `200`

Open http://localhost:8080/ in browser and verify:
- Dark `#24292f` nav with CrashWeb text and lightning bolt SVG icon
- Dashboard nav link has filled pill background `#373e47`
- Gray canvas background `#f6f8fa` (not white)
- Cards have border `1px solid #d0d7de`, no box-shadow
- Table headers are small (11px) uppercase gray text
- No broken layout, no missing content

- [ ] **Step 4: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/templates/base.html
git commit -m "style: rewrite base.html — GitHub-style palette, CrashWeb branding, pill nav"
```

---

### Task 2: dashboard.html

**Files:**
- Modify: `web/templates/dashboard.html`

Changes: title, stat card SVG icons + label renames, SDK card header border, SDK card footer palette, autolog button class, ticket row highlight, JS color strings.

- [ ] **Step 1: Update title**

Find:
```
{% block title %}Dashboard - Coredump Browser{% endblock %}
```
Replace with:
```
{% block title %}Dashboard · CrashWeb{% endblock %}
```

- [ ] **Step 2: Replace stat cards block (add SVG icons, rename labels)**

Find:
```html
    <a href="{{ url_for('cores') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="number">{{ "{:,}".format(total_cores) }}</div>
        <div class="label">Total Coredumps</div>
    </a>
    <a href="{{ url_for('devices') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="number">{{ total_devices }}</div>
        <div class="label">Devices</div>
    </a>
    <a href="{{ url_for('revisions') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="number">{{ total_revisions }}</div>
        <div class="label">SW Revisions</div>
    </a>
```
Replace with:
```html
    <a href="{{ url_for('cores') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg></div>
        <div class="number">{{ "{:,}".format(total_cores) }}</div>
        <div class="label">Cores</div>
    </a>
    <a href="{{ url_for('devices') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg></div>
        <div class="number">{{ total_devices }}</div>
        <div class="label">Devices</div>
    </a>
    <a href="{{ url_for('revisions') }}" class="stat-card" style="text-decoration:none;color:inherit;display:block">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg></div>
        <div class="number">{{ total_revisions }}</div>
        <div class="label">Revisions</div>
    </a>
```

- [ ] **Step 3: Update SDK card header (add border separator)**

Find:
```html
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <h2 style="margin:0">SDK Versions</h2>
        <a href="{{ url_for('revisions') }}" style="font-size:13px">View Revisions &rarr;</a>
    </div>
```
Replace with:
```html
    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #d0d7de;padding-bottom:12px;margin-bottom:16px">
        <h2 style="margin:0;border:none;padding:0">SDK Versions</h2>
        <a href="{{ url_for('revisions') }}" style="font-size:13px">View Revisions &rarr;</a>
    </div>
```

- [ ] **Step 4: Update SDK card footer (autolog bar palette)**

Find:
```html
    <div style="border-top:1px solid #eee;margin-top:10px;padding-top:8px;display:flex;align-items:center;gap:8px;font-size:0.82rem;background:#f8f9fa;margin-left:-20px;margin-right:-20px;padding-left:20px;padding-right:20px;padding-bottom:8px">
        <span style="color:#888">Auto-install (midnight &amp; reboot):</span>
        <span id="sdk-autolog-summary" style="color:#888;font-style:italic">checking&hellip;</span>
        <button onclick="document.getElementById('sdk-autolog-full').style.display=document.getElementById('sdk-autolog-full').style.display==='none'?'block':'none'" style="margin-left:auto;background:#6c757d;padding:2px 8px;font-size:0.7rem">&#128196; Log</button>
    </div>
```
Replace with:
```html
    <div style="border-top:1px solid #d0d7de;margin-top:10px;padding-top:8px;display:flex;align-items:center;gap:8px;font-size:0.82rem;background:#f6f8fa;margin-left:-20px;margin-right:-20px;padding-left:20px;padding-right:20px;padding-bottom:8px">
        <span style="color:#656d76">Auto-install (midnight &amp; reboot):</span>
        <span id="sdk-autolog-summary" style="color:#656d76;font-style:italic">checking&hellip;</span>
        <button onclick="document.getElementById('sdk-autolog-full').style.display=document.getElementById('sdk-autolog-full').style.display==='none'?'block':'none'" class="btn-ghost btn-sm" style="margin-left:auto">&#128196; Log</button>
    </div>
```

- [ ] **Step 5: Update autolog pre and ticket row highlight**

Find:
```html
        <pre id="sdk-autolog-body" style="margin:0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#666"></pre>
```
Replace with:
```html
        <pre id="sdk-autolog-body" style="margin:0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#656d76"></pre>
```

In the recent coredumps table row, find:
```
{% if t %} style="background:#f0f4ff"{% endif %}
```
Replace with:
```
{% if t %} style="background:#f6f8fa"{% endif %}
```

- [ ] **Step 6: Update JS color strings in dashboard.html scripts block**

These are all string literals inside JavaScript that build HTML for the SDK status UI. Make these replacements in the `{% block scripts %}` section:

| Find | Replace |
|------|---------|
| `color:#3498db` | `color:#0969da` |
| `background:#f0f4ff` | `background:#f6f8fa` |
| `color:#888;font-style:italic` (two occurrences in JS) | `color:#656d76;font-style:italic` |
| `color:#666` (in JS pre style string) | `color:#656d76` |

- [ ] **Step 7: Build, restart, verify dashboard**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

Open http://localhost:8080/ and verify:
- Stat cards show SVG icons (layers/Cores, cpu/Devices, tag/Revisions)
- SDK card has border separator under header
- Autolog footer is light gray background with ghost Log button
- "Top Crashing Binaries" card h2 has border-bottom separator

- [ ] **Step 8: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/templates/dashboard.html
git commit -m "style: update dashboard.html — stat card icons, SDK card palette, title"
```

---

### Task 3: cores.html

**Files:**
- Modify: `web/templates/cores.html`

- [ ] **Step 1: Update title and h1**

Find:
```
{% block title %}Coredumps{% endblock %}
```
Replace with:
```
{% block title %}Cores · CrashWeb{% endblock %}
```

Find:
```html
<h1>Coredumps</h1>
```
Replace with:
```html
<h1>Cores</h1>
```

- [ ] **Step 2: Add subtle background to filter card**

Find:
```html
<div class="card">
    <form method="GET" action="{{ url_for('cores') }}">
```
Replace with:
```html
<div class="card" style="background:#f6f8fa">
    <form method="GET" action="{{ url_for('cores') }}">
```

- [ ] **Step 3: Update signature filter banner**

Find:
```html
    <div style="margin-top: 12px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-size: 13px;">
```
Replace with:
```html
    <div style="margin-top: 12px; padding: 10px 14px; background: #fff8c5; border: 1px solid #d4a72c; border-radius: 6px; font-size: 13px;">
```

- [ ] **Step 4: Update Mark button to ghost style**

Find:
```html
                    <button class="btn btn-sm" style="background:#6c757d;font-size:11px;padding:2px 6px" onclick="openTicketForm(this,'{{ r[5] }}')">+ Mark</button>
```
Replace with:
```html
                    <button class="btn btn-sm btn-ghost" style="font-size:11px;padding:2px 6px" onclick="openTicketForm(this,'{{ r[5] }}')">+ Mark</button>
```

- [ ] **Step 5: Update ticket row highlight**

Find:
```
{% if t %} style="background:#f0f4ff"{% endif %}
```
Replace with:
```
{% if t %} style="background:#f6f8fa"{% endif %}
```

- [ ] **Step 6: Build, restart, verify**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

Open http://localhost:8080/cores and verify:
- h1 reads "Cores", browser tab shows "Cores · CrashWeb"
- Filter card has subtle gray `#f6f8fa` background
- Active signature filter banner shows amber border and yellow background
- Mark button is ghost style (light, not solid gray)

- [ ] **Step 7: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/templates/cores.html
git commit -m "style: update cores.html — title, filter card, signature banner, ghost mark button"
```

---

### Task 4: core_detail.html

**Files:**
- Modify: `web/templates/core_detail.html`

Tab styles (active underline `#0969da`, hover gray) are already handled by the base.html CSS rewrite in Task 1. No inline tab style changes needed here.

- [ ] **Step 1: Update title**

Find:
```
{% block title %}Core #{{ core.clc_id }}{% endblock %}
```
Replace with:
```
{% block title %}Core #{{ core.clc_id }} · CrashWeb{% endblock %}
```

- [ ] **Step 2: Update breadcrumb**

Find:
```html
    <a href="{{ url_for('cores') }}">Coredumps</a> / <strong>#{{ core.clc_id }}</strong>
```
Replace with:
```html
    <a href="{{ url_for('cores') }}">Cores</a> › <strong>#{{ core.clc_id }}</strong>
```

- [ ] **Step 3: Build, restart, verify**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

Open any core detail page (e.g. http://localhost:8080/core/1) and verify:
- Browser tab shows "Core #N · CrashWeb"
- Breadcrumb reads "Cores › #N"
- Cores nav link has active pill (since `core_detail` is in active condition)
- Active tab has blue underline `#0969da`
- Inactive tabs are muted gray, hover turns dark

- [ ] **Step 4: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/templates/core_detail.html
git commit -m "style: update core_detail.html — title, breadcrumb (Cores, › separator)"
```

---

### Task 5: Remaining templates

**Files:**
- Modify: `web/templates/revisions.html`
- Modify: `web/templates/devices.html`
- Modify: `web/templates/device_detail.html`
- Modify: `web/templates/analyze.html`
- Modify: `web/templates/error.html`

- [ ] **Step 1: revisions.html — title and h1**

Find:
```
{% block title %}SW Revisions{% endblock %}
```
Replace with:
```
{% block title %}Revisions · CrashWeb{% endblock %}
```

Find:
```html
<h1>Software Revisions</h1>
```
Replace with:
```html
<h1>Revisions</h1>
```

- [ ] **Step 2: devices.html — title**

Find:
```
{% block title %}Devices{% endblock %}
```
Replace with:
```
{% block title %}Devices · CrashWeb{% endblock %}
```

- [ ] **Step 3: device_detail.html — title and breadcrumb separator**

Find:
```
{% block title %}Device: {{ device.cla_eqm_name }}{% endblock %}
```
Replace with:
```
{% block title %}Device: {{ device.cla_eqm_name }} · CrashWeb{% endblock %}
```

Find:
```html
    <a href="{{ url_for('devices') }}">Devices</a> / <strong>{{ device.cla_eqm_name }}</strong>
```
Replace with:
```html
    <a href="{{ url_for('devices') }}">Devices</a> › <strong>{{ device.cla_eqm_name }}</strong>
```

- [ ] **Step 4: analyze.html — title, spinner color, border colors**

Find:
```
{% block title %}Analyze - {{ rev }}{% endblock %}
```
Replace with:
```
{% block title %}Analysis · CrashWeb{% endblock %}
```

Find:
```css
        .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid #ddd; border-top-color: #3498db; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: middle; }
```
Replace with:
```css
        .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid #d0d7de; border-top-color: #0969da; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: middle; }
```

Find:
```html
    <div id="loading-indicator" style="display: none; margin-top: 16px; padding: 16px; background: #f8f9fa; border-radius: 6px; text-align: center;">
```
Replace with:
```html
    <div id="loading-indicator" style="display: none; margin-top: 16px; padding: 16px; background: #f6f8fa; border-radius: 6px; text-align: center;">
```

Find (process group inner card border — two occurrences, one in stack group and one in process group):
```html
        <div style="border: 1px solid #eee; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
```
Replace with:
```html
        <div style="border: 1px solid #d0d7de; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
```

Find (more frames footer — two occurrences, one per group type):
```html
            <div style="font-size: 12px; color: #888; padding: 4px 10px; background: #f8f8f8; border-top: 1px solid #eee;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
```
Replace both occurrences with:
```html
            <div style="font-size: 12px; color: #656d76; padding: 4px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
```

- [ ] **Step 5: error.html — title**

Find:
```
{% block title %}Error{% endblock %}
```
Replace with:
```
{% block title %}Error · CrashWeb{% endblock %}
```

- [ ] **Step 6: Build, restart, verify all pages**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

Check each page:
- http://localhost:8080/revisions — title "Revisions · CrashWeb", h1 "Revisions", Revisions nav pill active
- http://localhost:8080/devices — title "Devices · CrashWeb", Devices nav pill active
- http://localhost:8080/analyze — title "Analysis · CrashWeb", Analysis nav pill active, spinner uses `#0969da`

- [ ] **Step 7: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/templates/revisions.html web/templates/devices.html web/templates/device_detail.html web/templates/analyze.html web/templates/error.html
git commit -m "style: update remaining templates — titles, breadcrumbs, analyze border/spinner colors"
```

---

### Task 6: Final verification and push

- [ ] **Step 1: Full smoke test**

Visit each route and confirm no regressions:

| URL | Verify |
|-----|--------|
| http://localhost:8080/ | Nav pill on Dashboard; stat cards with SVG icons; SDK card styled |
| http://localhost:8080/cores | Pill on Cores; filter card `#f6f8fa`; table headers uppercase gray |
| http://localhost:8080/cores?bt_csum=abc | Signature banner shows `#fff8c5` yellow + amber border |
| http://localhost:8080/devices | Pill on Devices; table renders correctly |
| http://localhost:8080/revisions | Pill on Revisions; h1 reads "Revisions" |
| http://localhost:8080/analyze | Pill on Analysis; blue spinner |
| http://localhost:8080/core/1 | Breadcrumb "Cores ›"; Cores pill active; tab underline `#0969da` |
| All pages | Title pattern "Page · CrashWeb" in browser tab |
| All pages | Signal badges still red/yellow — semantic colors unchanged |
| All pages | Cause/systematic badges still colored — semantic colors unchanged |
| All pages | No box shadows anywhere; all borders `1px solid #d0d7de` |

- [ ] **Step 2: Push to remote**

```bash
cd /home/sbera/git/personal/crashweb
GH_TOKEN=$(gh auth token --hostname github.com -u sberaconnects)
git remote set-url origin https://sberaconnects:${GH_TOKEN}@github.com/sberaconnects/crashweb.git
git push origin main
git remote set-url origin git@github.com:sberaconnects/crashweb.git
```

Expected: 5 commits pushed (one per task).
