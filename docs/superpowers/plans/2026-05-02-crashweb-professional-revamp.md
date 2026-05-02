# CrashWeb Professional Revamp — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul CrashWeb UI with Tokyo Night palette, fixed sidebar nav, renamed pages, and improved stat card/table typography.

**Architecture:** CSS-only color swap + sidebar layout change in base.html; per-template inline style and text updates in 7 child templates. No structural Jinja logic changes. No new dependencies.

**Tech Stack:** Flask/Jinja2 templates, inline CSS (`<style>` blocks + `style=` attrs), HTML.

---

### Task 1: base.html — Tokyo Night CSS + sidebar layout

**Files:**
- Modify: `web/templates/base.html`

Replace entire `<style>` block and `<nav>` HTML with Tokyo Night palette and fixed sidebar layout.

- [ ] **Step 1: Write new base.html**

Complete replacement of `web/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CrashWeb{% endblock %}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #1a1b26; color: #c0caf5; font-size: 14px; display: flex; min-height: 100vh; }

        /* --- Sidebar --- */
        .sidebar { width: 220px; min-height: 100vh; background: #16161e; border-right: 1px solid #414868; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; z-index: 100; }
        .sidebar-brand { padding: 20px 16px 16px; display: flex; align-items: center; gap: 10px; color: #c0caf5; font-weight: 700; font-size: 15px; text-decoration: none; border-bottom: 1px solid #414868; margin-bottom: 8px; }
        .sidebar-brand:hover { color: #c0caf5; text-decoration: none; }
        .sidebar-brand svg { color: #7aa2f7; flex-shrink: 0; }
        .sidebar-nav { flex: 1; padding: 4px 0; }
        .sidebar-nav a { display: flex; align-items: center; gap: 10px; padding: 9px 16px; color: #565f89; text-decoration: none; font-size: 13px; font-weight: 500; border-left: 3px solid transparent; transition: color 0.1s, background 0.1s, border-color 0.1s; }
        .sidebar-nav a:hover { color: #c0caf5; background: rgba(122,162,247,0.06); text-decoration: none; }
        .sidebar-nav a.active { color: #7aa2f7; background: rgba(122,162,247,0.08); border-left-color: #7aa2f7; }
        .sidebar-nav a svg { opacity: 0.7; flex-shrink: 0; }
        .sidebar-nav a.active svg { opacity: 1; }
        .sidebar-footer { padding: 12px 16px; border-top: 1px solid #414868; font-size: 11px; color: #414868; }

        /* --- Main content --- */
        .main { margin-left: 220px; flex: 1; padding: 28px 32px; min-width: 0; }

        /* --- Page header --- */
        .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
        .page-header h1 { font-size: 24px; font-weight: 700; color: #c0caf5; }
        h1 { font-size: 24px; font-weight: 700; margin-bottom: 24px; }

        /* --- Breadcrumb --- */
        .breadcrumb { margin-bottom: 16px; font-size: 13px; color: #565f89; }
        .breadcrumb a { color: #7aa2f7; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }

        /* --- Cards --- */
        .card { background: #24283b; border-radius: 8px; border: 1px solid #414868; padding: 20px; margin-bottom: 20px; }
        .card > h2:not(.process-header) { font-size: 11px; color: #565f89; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; border-bottom: 1px solid #414868; padding-bottom: 10px; margin-bottom: 16px; }
        .card > h2.process-header { font-size: 11px; color: #565f89; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }

        /* --- Tables --- */
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #414868; }
        th { background: #24283b; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #565f89; position: sticky; top: 0; white-space: nowrap; }
        tbody tr:last-child td { border-bottom: none; }
        tbody tr:hover { background: #2f3354; }
        .table-wrapper { overflow-x: auto; max-height: 70vh; overflow-y: auto; }

        /* --- Links --- */
        a { color: #7aa2f7; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* --- Inputs --- */
        textarea { width: 100%; min-height: 100px; padding: 12px; font-family: "JetBrains Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; border: 1px solid #414868; border-radius: 6px; resize: vertical; background: #24283b; color: #c0caf5; }
        textarea:focus { outline: 2px solid #7aa2f7; outline-offset: 0; }
        input[type="text"], select { padding: 6px 10px; border: 1px solid #414868; border-radius: 6px; font-size: 13px; background: #24283b; color: #c0caf5; }
        input[type="text"]:focus, select:focus { outline: 2px solid #7aa2f7; outline-offset: 0; }

        /* --- Buttons --- */
        button, .btn { background: #7aa2f7; color: #1a1b26; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; display: inline-block; text-decoration: none; transition: background 0.1s; }
        button:hover, .btn:hover { background: #89b4fa; text-decoration: none; }
        .btn-sm { padding: 4px 10px; font-size: 12px; }
        .btn-ghost { background: #2f3354; color: #c0caf5; border: 1px solid #414868; }
        .btn-ghost:hover { background: #414868; }
        .btn-danger { background: #f7768e; color: #1a1b26; border: none; }
        .btn-danger:hover { background: #ff8fa3; }

        /* --- Error --- */
        .error { background: rgba(247,118,142,0.12); border: 1px solid rgba(247,118,142,0.4); color: #f7768e; padding: 12px; border-radius: 6px; margin-bottom: 16px; }

        /* --- Pagination --- */
        .pagination { margin-top: 16px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
        .pagination a, .pagination span { padding: 5px 10px; border: 1px solid #414868; border-radius: 6px; text-decoration: none; color: #c0caf5; font-size: 13px; }
        .pagination a:hover { background: #2f3354; text-decoration: none; }
        .pagination .active { background: #7aa2f7; color: #1a1b26; border-color: #7aa2f7; font-weight: 600; }

        /* --- Meta --- */
        .meta { color: #565f89; font-size: 13px; margin-bottom: 12px; }

        /* --- Truncate --- */
        td.truncate { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        td.truncate:hover { white-space: normal; word-break: break-all; }

        /* --- Stat cards --- */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: #24283b; border-radius: 8px; border: 1px solid #414868; padding: 20px; text-align: center; cursor: pointer; transition: background 0.1s, border-color 0.1s; position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent-bar, #7aa2f7); }
        .stat-card:hover { background: #2f3354; border-color: #7aa2f7; text-decoration: none; }
        .stat-card .stat-icon { color: #565f89; margin-bottom: 10px; display: flex; justify-content: center; }
        .stat-card .number { font-size: 40px; font-weight: 700; color: #c0caf5; line-height: 1; }
        .stat-card .label { font-size: 11px; color: #565f89; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }

        /* --- Filters --- */
        .filters { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; margin-bottom: 16px; }
        .filters label { font-size: 12px; font-weight: 600; color: #565f89; display: block; margin-bottom: 3px; }

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
        .pre-wrap .copy-btn { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.06); color: #c0caf5; border: 1px solid rgba(255,255,255,0.12); padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; opacity: 0.8; transition: opacity 0.15s, background 0.15s; }
        .pre-wrap .copy-btn:hover { opacity: 1; background: rgba(255,255,255,0.12); }
        .pre-wrap .copy-btn.copied { background: #9ece6a; border-color: #9ece6a; color: #1a1b26; opacity: 1; }
        pre { background: #16161e; color: #c0caf5; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.6; font-family: "JetBrains Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; border: 1px solid #414868; }
        pre .line-no { color: #414868; user-select: none; display: inline-block; width: 40px; text-align: right; margin-right: 16px; }

        /* --- Tabs --- */
        .tabs { display: flex; border-bottom: 1px solid #414868; margin-bottom: 16px; }
        .tab { padding: 8px 16px; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; font-weight: 500; color: #565f89; }
        .tab.active { color: #c0caf5; border-bottom-color: #7aa2f7; }
        .tab:hover { color: #c0caf5; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* --- Detail grid --- */
        .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .detail-grid .field-label { font-size: 11px; font-weight: 600; color: #565f89; text-transform: uppercase; letter-spacing: 0.5px; }
        .detail-grid .field-value { font-size: 14px; margin-top: 2px; }

        /* --- Badges (semantic — unchanged) --- */
        .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
        .badge + .badge { margin-left: 4px; }
    </style>
</head>
<body>
    <aside class="sidebar">
        <a class="sidebar-brand" href="{{ url_for('index') }}">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            CrashWeb
        </a>
        <nav class="sidebar-nav">
            <a class="{% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                Overview
            </a>
            <a class="{% if request.endpoint in ('cores', 'core_detail') %}active{% endif %}" href="{{ url_for('cores') }}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                Crashes
            </a>
            <a class="{% if request.endpoint in ('devices', 'device_detail') %}active{% endif %}" href="{{ url_for('devices') }}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>
                Devices
            </a>
            <a class="{% if request.endpoint == 'revisions' %}active{% endif %}" href="{{ url_for('revisions') }}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
                Firmware
            </a>
            <a class="{% if request.endpoint == 'analyze' %}active{% endif %}" href="{{ url_for('analyze') }}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                Patterns
            </a>
        </nav>
        <div class="sidebar-footer">CrashWeb</div>
    </aside>
    <div class="main">
        {% block content %}{% endblock %}
    </div>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Verify file written**

Open `web/templates/base.html` and confirm: `sidebar` class present, `#1a1b26` canvas color present, `Overview`/`Crashes`/`Firmware`/`Patterns` nav labels present.

- [ ] **Step 3: Commit**

```bash
git add web/templates/base.html
git commit -m "feat: Tokyo Night palette + sidebar nav in base.html"
```

---

### Task 2: dashboard.html — rename + stat accent bars + inline color updates

**Files:**
- Modify: `web/templates/dashboard.html`

- [ ] **Step 1: Read current file**

Read `web/templates/dashboard.html` in full.

- [ ] **Step 2: Apply all changes**

Changes to make:
1. `{% block title %}Dashboard` → `{% block title %}Overview`
2. `<h1>Dashboard</h1>` → `<h1>Overview</h1>`
3. Stat card for Cores: add `style="--accent-bar:#7aa2f7"` to `.stat-card` anchor, change `<div class="label">Cores</div>` → `<div class="label">Crashes</div>`
4. Stat card for Devices: add `style="--accent-bar:#e0af68"` to `.stat-card` anchor
5. Stat card for Revisions: add `style="--accent-bar:#9ece6a"` to `.stat-card` anchor, change `<div class="label">Revisions</div>` → `<div class="label">Firmware</div>`
6. SDK card border color `#4c566a` → `#414868`
7. Footer bar in SDK card: `background:#3b4252` → `background:#2f3354`, `border-top:1px solid #4c566a` → `border-top:1px solid #414868`
8. All `color:#d8dee9` → `color:#565f89`
9. All `color:#656d76` → `color:#565f89`
10. All `border-color:#4c566a` → `border-color:#414868`
11. Ticket row highlight `#434c5e` → `#2f3354`
12. JS status colors in `<script>`: `#bf616a` → `#f7768e`, `#a3be8c` → `#9ece6a`, `#d8dee9` → `#565f89`, `#4c566a` → `#414868`
13. `border-bottom:1px solid #4c566a` → `border-bottom:1px solid #414868`

Use Edit tool for each change. Make all changes before committing.

- [ ] **Step 3: Commit**

```bash
git add web/templates/dashboard.html
git commit -m "feat: rename Dashboard→Overview, update inline colors"
```

---

### Task 3: cores.html + core_detail.html — rename + inline color updates

**Files:**
- Modify: `web/templates/cores.html`
- Modify: `web/templates/core_detail.html`

- [ ] **Step 1: Read both files in full**

- [ ] **Step 2: Update cores.html**

Changes:
1. `{% block title %}Cores` → `{% block title %}Crashes`
2. `<h1>Cores</h1>` → `<h1>Crashes</h1>` (or similar h1 text)
3. Filter card bg `#3b4252` → `#24283b`
4. All border colors `#4c566a` → `#414868`
5. Signature banner: `rgba(235,203,139,0.12)` → `rgba(224,175,104,0.12)`, `rgba(235,203,139,0.5)` → `rgba(224,175,104,0.4)`
6. Ticket row `#434c5e` → `#2f3354`
7. Ticket badge `#5e81ac` → `#7aa2f7`
8. All `color:#d8dee9` → `color:#565f89`
9. All `color:#656d76` → `color:#565f89`

- [ ] **Step 3: Update core_detail.html**

Changes:
1. Filter/bg `#3b4252` → `#24283b`
2. All border `#4c566a` → `#414868`
3. SDK banner warning `rgba(235,203,139,0.12)` → `rgba(224,175,104,0.12)`, border `rgba(235,203,139,0.5)` → `rgba(224,175,104,0.4)`, text `#ebcb8b` → `#e0af68`
4. SDK install btn `#ebcb8b` → `#e0af68`, color `#3b4252` → `#1a1b26`
5. SDK success `rgba(163,190,140,0.12)` → `rgba(158,206,106,0.12)`, border/text → `#9ece6a`
6. SDK info `rgba(136,192,208,0.12)` → `rgba(122,162,247,0.1)`, text `#81a1c1` → `#7aa2f7`
7. SDK process btn `#a3be8c` → `#9ece6a`, color `#3b4252` → `#1a1b26`
8. GH issue prompt colors: background `#3b4252` → `#24283b`, border `#4c566a` → `#414868`
9. All `color:#d8dee9` → `color:#565f89`
10. Mark-analyzed btn: `#5e81ac` → `#7aa2f7`

- [ ] **Step 4: Commit**

```bash
git add web/templates/cores.html web/templates/core_detail.html
git commit -m "feat: rename Cores→Crashes, update inline colors"
```

---

### Task 4: analyze.html + revisions.html + devices.html + device_detail.html

**Files:**
- Modify: `web/templates/analyze.html`
- Modify: `web/templates/revisions.html`
- Modify: `web/templates/devices.html`
- Modify: `web/templates/device_detail.html`

- [ ] **Step 1: Read all four files in full**

- [ ] **Step 2: Update analyze.html**

Changes:
1. `{% block title %}Analysis` → `{% block title %}Patterns`
2. `<h1>...Analysis...</h1>` → change "Analysis" to "Patterns" in page title area
3. Spinner track `#4c566a` → `#414868`, spinner head `#5e81ac` → `#7aa2f7`
4. Loading bg `#3b4252` → `#24283b`, text `#d8dee9` → `#565f89`
5. Process pill bg `#434c5e` → `#2f3354`
6. Group card border `#4c566a` → `#414868`
7. Device badge bg `rgba(94,129,172,0.15)` → `rgba(122,162,247,0.12)`, color `#81a1c1` → `#7aa2f7`
8. No-backtrace color `#6c7a8a` → `#565f89`
9. All `color:#d8dee9` → `color:#565f89`
10. All `color:#656d76` → `color:#565f89`
11. Proc badge `#434c5e` → `#2f3354`

- [ ] **Step 3: Update revisions.html**

Changes:
1. `{% block title %}Revisions` → `{% block title %}Firmware`
2. `<h1>Revisions</h1>` → `<h1>Firmware</h1>`
3. Any inline `#4c566a` → `#414868`, `#3b4252` → `#24283b`, `#d8dee9`/`#656d76` → `#565f89`, `#5e81ac` → `#7aa2f7`, `#a3be8c` → `#9ece6a`, `#ebcb8b` → `#e0af68`

- [ ] **Step 4: Update devices.html + device_detail.html**

For each file, replace any inline Nord colors with Tokyo Night equivalents:
- `#4c566a` → `#414868`
- `#3b4252` → `#24283b`
- `#d8dee9` / `#656d76` → `#565f89`
- `#5e81ac` → `#7aa2f7`
- `#eceff4` → `#c0caf5`
- `#bf616a` → `#f7768e`

- [ ] **Step 5: Commit**

```bash
git add web/templates/analyze.html web/templates/revisions.html web/templates/devices.html web/templates/device_detail.html
git commit -m "feat: rename Analysis→Patterns, Revisions→Firmware, update inline colors"
```

---

### Task 5: Build Docker image and verify

**Files:** none (shell commands only)

- [ ] **Step 1: Rebuild flask-web image**

```bash
cd /home/sbera/git/personal/crashweb
docker compose -f docker-compose.yml -f docker-compose-local.yml build flask-web
```

Expected: Build completes with exit 0.

- [ ] **Step 2: Restart flask-web container**

```bash
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d flask-web
```

Expected: Container starts, `docker compose ps` shows flask-web running.

- [ ] **Step 3: Verify UI accessible**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
```

Expected: `200`

- [ ] **Step 4: Check sidebar present in HTML output**

```bash
curl -s http://localhost:8080/ | grep -c "sidebar"
```

Expected: number > 0

- [ ] **Step 5: Commit docs**

```bash
git add docs/superpowers/specs/2026-05-02-crashweb-professional-revamp-design.md docs/superpowers/plans/2026-05-02-crashweb-professional-revamp.md
git commit -m "docs: professional revamp spec and plan"
```

