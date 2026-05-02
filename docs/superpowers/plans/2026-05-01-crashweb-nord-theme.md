# CrashWeb Nord Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the GitHub slate color palette with the Nord palette across all CrashWeb Jinja2 templates — CSS-only, no structural changes.

**Architecture:** Four tasks. Task 1 rewrites the global `<style>` block in `base.html`. Tasks 2–4 update per-template inline `style=` attributes and JavaScript color string literals. No Python changes. No new files.

**Tech Stack:** Jinja2 HTML templates, inline CSS, vanilla JS — Flask/Docker stack at `/home/sbera/git/personal/crashweb/`.

**Nord palette quick reference (used throughout):**

| Token | Value |
|-------|-------|
| Polar Night 0 (canvas) | `#2e3440` |
| Polar Night 1 (surface) | `#3b4252` |
| Polar Night 2 (subtle/hover) | `#434c5e` |
| Polar Night 3 (border/ghost btn) | `#4c566a` |
| Snow Storm 0 (muted text) | `#d8dee9` |
| Snow Storm 2 (body text) | `#eceff4` |
| Frost 2 (accent hover) | `#81a1c1` |
| Frost 3 (primary accent) | `#5e81ac` |
| Aurora red | `#bf616a` |
| Aurora yellow | `#ebcb8b` |
| Aurora green | `#a3be8c` |
| Nav bg | `#242933` |
| Code bg | `#242933` |

**Branch:** `nord-theme` (already created). Work in `/home/sbera/git/personal/crashweb/web/templates/`.

---

### Task 1: Rewrite base.html `<style>` block with Nord palette

**Files:**
- Modify: `web/templates/base.html` (lines 7–123: entire `<style>` block)

- [ ] **Step 1: Verify old GitHub palette present**

```bash
grep -c "#24292f\|#f6f8fa\|#d0d7de\|#0969da\|#1f2328" web/templates/base.html
```

Expected: number > 0 (confirms starting from GitHub slate).

- [ ] **Step 2: Replace the entire `<style>` block**

Open `web/templates/base.html`. Find the `<style>` block (lines 7–123). Replace the entire block:

old_string starts with `    <style>` and ends with `    </style>` (the full style block before `</head>`).

new_string (complete replacement):

```html
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; background: #2e3440; color: #eceff4; font-size: 14px; }

        /* --- Nav --- */
        nav { background: #242933; padding: 0 24px; display: flex; align-items: center; gap: 0; }
        nav a.brand { color: #fff; font-weight: 600; font-size: 15px; padding: 12px 20px 12px 0; margin-right: 4px; text-decoration: none; display: flex; align-items: center; gap: 8px; }
        nav a.brand:hover { color: #fff; text-decoration: none; }
        nav a.nav-link { color: rgba(255,255,255,0.7); text-decoration: none; font-weight: 500; padding: 6px 12px; border-radius: 6px; transition: color 0.1s, background 0.1s; }
        nav a.nav-link:hover { color: #fff; text-decoration: none; background: rgba(255,255,255,0.06); }
        nav a.nav-link.active { color: #fff; background: #4c566a; }

        /* --- Layout --- */
        .container { margin: 20px auto; padding: 0 24px; }

        /* --- Breadcrumb --- */
        .breadcrumb { margin-bottom: 16px; font-size: 13px; color: #d8dee9; }
        .breadcrumb a { color: #5e81ac; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }

        /* --- Cards --- */
        .card { background: #3b4252; border-radius: 6px; border: 1px solid #4c566a; padding: 20px; margin-bottom: 20px; }
        .card > h2:not(.process-header) { font-size: 16px; color: #eceff4; border-bottom: 1px solid #4c566a; padding-bottom: 12px; margin-bottom: 16px; }
        .card > h2.process-header { font-size: 16px; color: #eceff4; }
        h1 { font-size: 22px; margin-bottom: 16px; }

        /* --- Tables --- */
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #4c566a; }
        th { background: #3b4252; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #d8dee9; position: sticky; top: 0; white-space: nowrap; }
        tbody tr:last-child td { border-bottom: none; }
        tbody tr:hover { background: #434c5e; }
        .table-wrapper { overflow-x: auto; max-height: 70vh; overflow-y: auto; }

        /* --- Links --- */
        a { color: #5e81ac; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* --- Inputs --- */
        textarea { width: 100%; min-height: 100px; padding: 12px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; border: 1px solid #4c566a; border-radius: 6px; resize: vertical; background: #3b4252; color: #eceff4; }
        textarea:focus { outline: 2px solid #5e81ac; outline-offset: 0; }
        input[type="text"], select { padding: 6px 10px; border: 1px solid #4c566a; border-radius: 6px; font-size: 13px; background: #3b4252; color: #eceff4; }
        input[type="text"]:focus, select:focus { outline: 2px solid #5e81ac; outline-offset: 0; }

        /* --- Buttons --- */
        button, .btn { background: #5e81ac; color: #eceff4; border: 1px solid rgba(0,0,0,0.3); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; display: inline-block; text-decoration: none; }
        button:hover, .btn:hover { background: #81a1c1; text-decoration: none; }
        .btn-sm { padding: 4px 10px; font-size: 12px; }
        .btn-ghost { background: #434c5e; color: #eceff4; border: 1px solid #4c566a; }
        .btn-ghost:hover { background: #4c566a; }
        .btn-danger { background: #bf616a; border-color: transparent; color: #fff; }
        .btn-danger:hover { background: #a0505a; }

        /* --- Error --- */
        .error { background: rgba(191,97,106,0.15); border: 1px solid rgba(191,97,106,0.5); color: #bf616a; padding: 12px; border-radius: 6px; margin-bottom: 16px; }

        /* --- Pagination --- */
        .pagination { margin-top: 16px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
        .pagination a, .pagination span { padding: 5px 10px; border: 1px solid #4c566a; border-radius: 6px; text-decoration: none; color: #eceff4; font-size: 13px; }
        .pagination a:hover { background: #434c5e; text-decoration: none; }
        .pagination .active { background: #5e81ac; color: #fff; border-color: #5e81ac; }

        /* --- Meta --- */
        .meta { color: #d8dee9; font-size: 13px; margin-bottom: 12px; }

        /* --- Truncate --- */
        td.truncate { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        td.truncate:hover { white-space: normal; word-break: break-all; }

        /* --- Stat cards --- */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .stat-card { background: #3b4252; border-radius: 6px; border: 1px solid #4c566a; padding: 20px; text-align: center; cursor: pointer; transition: background 0.1s, border-color 0.1s; }
        .stat-card:hover { background: #434c5e; border-color: #81a1c1; text-decoration: none; }
        .stat-card .stat-icon { color: #d8dee9; margin-bottom: 8px; display: flex; justify-content: center; }
        .stat-card .number { font-size: 32px; font-weight: 700; color: #eceff4; }
        .stat-card .label { font-size: 13px; color: #d8dee9; margin-top: 4px; }

        /* --- Filters --- */
        .filters { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; margin-bottom: 16px; }
        .filters label { font-size: 12px; font-weight: 600; color: #d8dee9; display: block; margin-bottom: 3px; }

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
        .pre-wrap .copy-btn { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.08); color: #eceff4; border: 1px solid rgba(255,255,255,0.15); padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; opacity: 0.85; transition: opacity 0.15s, background 0.15s; }
        .pre-wrap .copy-btn:hover { opacity: 1; background: rgba(255,255,255,0.15); }
        .pre-wrap .copy-btn.copied { background: #a3be8c; border-color: #a3be8c; color: #2e3440; opacity: 1; }
        pre { background: #242933; color: #eceff4; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.5; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }
        pre .line-no { color: #d8dee9; user-select: none; display: inline-block; width: 40px; text-align: right; margin-right: 16px; }

        /* --- Tabs --- */
        .tabs { display: flex; border-bottom: 1px solid #4c566a; margin-bottom: 16px; }
        .tab { padding: 8px 16px; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; font-weight: 500; color: #d8dee9; }
        .tab.active { color: #eceff4; border-bottom-color: #5e81ac; }
        .tab:hover { color: #eceff4; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* --- Detail grid --- */
        .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .detail-grid .field-label { font-size: 11px; font-weight: 600; color: #d8dee9; text-transform: uppercase; letter-spacing: 0.5px; }
        .detail-grid .field-value { font-size: 14px; margin-top: 2px; }

        /* --- Badges (semantic — unchanged) --- */
        .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
        .badge + .badge { margin-left: 4px; }
    </style>
```

Use the Edit tool: old_string = the entire current `<style>` block (from `    <style>` through `    </style>`), new_string = the block above.

- [ ] **Step 3: Verify Nord palette applied**

```bash
grep -c "#2e3440\|#3b4252\|#4c566a\|#5e81ac\|#eceff4" web/templates/base.html
```

Expected: number > 0.

```bash
grep -c "#24292f\|#f6f8fa\|#d0d7de\|#0969da\|#1f2328\|#656d76" web/templates/base.html
```

Expected: `0` (no old GitHub palette left).

- [ ] **Step 4: Commit**

```bash
git add web/templates/base.html
git commit -m "style: apply Nord palette to base.html CSS"
```

---

### Task 2: Update dashboard.html inline styles and JS color strings

**Files:**
- Modify: `web/templates/dashboard.html`

Apply all changes below using the Edit tool.

- [ ] **Step 1: Verify old colors present**

```bash
grep -c "#d0d7de\|#f6f8fa\|#656d76\|#0d6efd\|#198754\|#dc3545\|#0969da" web/templates/dashboard.html
```

Expected: number > 0.

- [ ] **Step 2: SDK card header border**

old:
```
border-bottom:1px solid #d0d7de;padding-bottom:12px;margin-bottom:16px
```
new:
```
border-bottom:1px solid #4c566a;padding-bottom:12px;margin-bottom:16px
```

- [ ] **Step 3: "Checking SDK status" muted span**

old:
```
<span style="color:#656d76;font-style:italic">Checking SDK status&hellip;</span>
```
new:
```
<span style="color:#d8dee9;font-style:italic">Checking SDK status&hellip;</span>
```

- [ ] **Step 4: Autolog footer bar**

old:
```
border-top:1px solid #d0d7de;margin-top:10px;padding-top:8px;display:flex;align-items:center;gap:8px;font-size:0.82rem;background:#f6f8fa;margin-left:-20px;margin-right:-20px;padding-left:20px;padding-right:20px;padding-bottom:8px
```
new:
```
border-top:1px solid #4c566a;margin-top:10px;padding-top:8px;display:flex;align-items:center;gap:8px;font-size:0.82rem;background:#3b4252;margin-left:-20px;margin-right:-20px;padding-left:20px;padding-right:20px;padding-bottom:8px
```

- [ ] **Step 5: Autolog "Auto-install" and "checking…" spans**

old:
```
<span style="color:#656d76">Auto-install (midnight &amp; reboot):</span>
        <span id="sdk-autolog-summary" style="color:#656d76;font-style:italic">checking&hellip;</span>
```
new:
```
<span style="color:#d8dee9">Auto-install (midnight &amp; reboot):</span>
        <span id="sdk-autolog-summary" style="color:#d8dee9;font-style:italic">checking&hellip;</span>
```

- [ ] **Step 6: Autolog pre element**

old:
```
<pre id="sdk-autolog-body" style="margin:0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#656d76"></pre>
```
new:
```
<pre id="sdk-autolog-body" style="margin:0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#d8dee9"></pre>
```

- [ ] **Step 7: Systematic badge**

old:
```
<span class="badge" style="background:#dc3545;color:#fff" title="Same crash signature seen on multiple devices">&#9888; Systematic</span>
```
new:
```
<span class="badge" style="background:#bf616a;color:#fff" title="Same crash signature seen on multiple devices">&#9888; Systematic</span>
```

- [ ] **Step 8: "Crashes per Device" muted revision label**

old:
```
<h2>Crashes per Device <span style="font-size:12px; font-weight:normal; color:#656d76;">({{ newest_rev }})</span></h2>
```
new:
```
<h2>Crashes per Device <span style="font-size:12px; font-weight:normal; color:#d8dee9;">({{ newest_rev }})</span></h2>
```

- [ ] **Step 9: Ticket row highlight**

old:
```
<tr{% if t %} style="background:#f6f8fa"{% endif %}>
```
new:
```
<tr{% if t %} style="background:#434c5e"{% endif %}>
```

- [ ] **Step 10: Ticket badge (blue → frost)**

old:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff">{{ t.issue }}</span>{% endif %}
                {% endif %}
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    <p style="margin-top: 12px;">
```
new:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#5e81ac;color:#fff;text-decoration:none">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#5e81ac;color:#fff">{{ t.issue }}</span>{% endif %}
                {% endif %}
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    <p style="margin-top: 12px;">
```

- [ ] **Step 11: JS — Installation complete badge**

old:
```
? '<span class="badge" style="background:#198754;color:#fff">&#10003; Installation complete</span>'
```
new:
```
? '<span class="badge" style="background:#a3be8c;color:#2e3440">&#10003; Installation complete</span>'
```

NOTE: In the actual file (line 145) there are no backslash-escapes — the string delimiter is a single-quote and the content uses double-quotes. Show the Edit old_string as the exact line from the file:

old (exact from file line 145):
```
            ? '<span class="badge" style="background:#198754;color:#fff">&#10003; Installation complete</span>'
```
new:
```
            ? '<span class="badge" style="background:#a3be8c;color:#2e3440">&#10003; Installation complete</span>'
```

- [ ] **Step 12: JS — Failed badge**

old:
```
                ? '<span class="badge" style="background:#dc3545;color:#fff">Failed</span>'
```
new:
```
                ? '<span class="badge" style="background:#bf616a;color:#fff">Failed</span>'
```

- [ ] **Step 13: JS — Installing… color**

old:
```
                : '<span style="color:#0969da;font-weight:600">Installing&hellip;</span>');
```
new:
```
                : '<span style="color:#5e81ac;font-weight:600">Installing&hellip;</span>');
```

- [ ] **Step 14: JS — pre color in install log**

old:
```
'<pre style="margin:4px 0 0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#656d76">'
```
new:
```
'<pre style="margin:4px 0 0;font-size:0.75rem;max-height:120px;overflow:auto;white-space:pre-wrap;color:#d8dee9">'
```

- [ ] **Step 15: JS — No SDKs installed label**

old:
```
html += '<span style="color:#656d76;font-style:italic">No SDKs installed</span>';
```
new:
```
html += '<span style="color:#d8dee9;font-style:italic">No SDKs installed</span>';
```

- [ ] **Step 16: JS — Installed badge**

old:
```
html += '<span class="badge" style="background:#198754;color:#fff;margin-left:4px">&#10003; Installed</span>';
```
new:
```
html += '<span class="badge" style="background:#a3be8c;color:#2e3440;margin-left:4px">&#10003; Installed</span>';
```

- [ ] **Step 17: JS — Remote not configured label**

old:
```
html += '<span style="color:#656d76;font-style:italic;margin-left:12px">Remote SDK install not configured (set SDK_BASE_URL)</span>';
```
new:
```
html += '<span style="color:#d8dee9;font-style:italic;margin-left:12px">Remote SDK install not configured (set SDK_BASE_URL)</span>';
```

- [ ] **Step 18: JS — Install log container div**

old:
```
html += '<div style="margin-top:8px;padding:8px;background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;font-size:0.85rem">';
```
new:
```
html += '<div style="margin-top:8px;padding:8px;background:#3b4252;border:1px solid #4c566a;border-radius:6px;font-size:0.85rem">';
```

- [ ] **Step 19: JS — Fetching log color**

old:
```
html += '<strong>Installing ' + iv + ':</strong> <span id="sdk-install-log-' + iv + '"><span style="color:#0969da">Fetching log&hellip;</span></span>';
```
new:
```
html += '<strong>Installing ' + iv + ':</strong> <span id="sdk-install-log-' + iv + '"><span style="color:#5e81ac">Fetching log&hellip;</span></span>';
```

- [ ] **Step 20: JS — SDK status unavailable span**

Find this string in the refreshSdk `.catch` handler (line ~197):

old:
```
'<span style="color:#dc3545">SDK status unavailable</span>'
```
new:
```
'<span style="color:#bf616a">SDK status unavailable</span>'
```

- [ ] **Step 21: JS — autolog FAILED color**

old:
```
summary.textContent = prefix + ' \u2014 FAILED'; summary.style.color = '#dc3545';
```

NOTE: Use the exact file content (line ~237):

old:
```
summary.textContent = prefix + ' — FAILED'; summary.style.color = '#dc3545'; summary.style.fontWeight = '600';
```
new:
```
summary.textContent = prefix + ' — FAILED'; summary.style.color = '#bf616a'; summary.style.fontWeight = '600';
```

- [ ] **Step 22: JS — autolog installed OK color**

old:
```
summary.textContent = prefix + ' — installed OK'; summary.style.color = '#198754'; summary.style.fontWeight = '600';
```
new:
```
summary.textContent = prefix + ' — installed OK'; summary.style.color = '#a3be8c'; summary.style.fontWeight = '600';
```

- [ ] **Step 23: JS — autolog up-to-date color**

old:
```
summary.textContent = prefix + ' — up-to-date'; summary.style.color = '#198754'; summary.style.fontWeight = '';
```
new:
```
summary.textContent = prefix + ' — up-to-date'; summary.style.color = '#a3be8c'; summary.style.fontWeight = '';
```

- [ ] **Step 24: JS — autolog fallback color**

old:
```
summary.style.color = '#656d76'; summary.style.fontWeight = '';
```
new:
```
summary.style.color = '#d8dee9'; summary.style.fontWeight = '';
```

- [ ] **Step 25: Verify no old palette colors remain**

```bash
grep -n "#d0d7de\|#f6f8fa\|#656d76\|#0d6efd\|#198754\|#dc3545\|#0969da" web/templates/dashboard.html
```

Expected: no output. Fix any remaining lines before committing.

- [ ] **Step 26: Commit**

```bash
git add web/templates/dashboard.html
git commit -m "style: apply Nord palette to dashboard.html"
```

---

### Task 3: Update cores.html and core_detail.html inline styles

**Files:**
- Modify: `web/templates/cores.html`
- Modify: `web/templates/core_detail.html`

#### cores.html changes

- [ ] **Step 1: Filter card background**

old:
```
<div class="card" style="background:#f6f8fa">
```
new:
```
<div class="card" style="background:#3b4252">
```

- [ ] **Step 2: Signature filter banner**

old:
```
<div style="margin-top: 12px; padding: 10px 14px; background: #fff8c5; border: 1px solid #d4a72c; border-radius: 6px; font-size: 13px;">
```
new:
```
<div style="margin-top: 12px; padding: 10px 14px; background: rgba(235,203,139,0.12); border: 1px solid rgba(235,203,139,0.5); border-radius: 6px; font-size: 13px;">
```

- [ ] **Step 3: Ticket row highlight**

old:
```
<tr{% if t %} style="background:#f6f8fa"{% endif %}>
                <td><a href="{{ url_for('core_detail', core_id=r[0]) }}">#{{ r[0] }}</a></td>
```

NOTE: Use exact file content (no escaping needed in the Edit tool):

old:
```
<tr{% if t %} style="background:#f6f8fa"{% endif %}>
                <td><a href="{{ url_for('core_detail', core_id=r[0]) }}">#{{ r[0] }}</a></td>
```
new:
```
<tr{% if t %} style="background:#434c5e"{% endif %}>
                <td><a href="{{ url_for('core_detail', core_id=r[0]) }}">#{{ r[0] }}</a></td>
```

- [ ] **Step 4: Ticket badge**

old:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff">{{ t.issue }}</span>{% endif %}
                {% elif r[5] %}
```
new:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#5e81ac;color:#fff;text-decoration:none">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#5e81ac;color:#fff">{{ t.issue }}</span>{% endif %}
                {% elif r[5] %}
```

- [ ] **Step 5: Cancel button in ticket form JS**

old:
```
+ ' <button class="btn btn-sm" style="background:#6c757d;font-size:11px" onclick="location.reload()">\u2715</button>';
```

NOTE: Use exact file content:

old:
```
        + ' <button class="btn btn-sm" style="background:#6c757d;font-size:11px" onclick="location.reload()">✕</button>';
```
new:
```
        + ' <button class="btn btn-sm" style="background:#4c566a;font-size:11px" onclick="location.reload()">✕</button>';
```

#### core_detail.html changes

- [ ] **Step 6: Download SDK button**

old:
```
<a href="{{ sdk_download_url }}" class="btn btn-sm" style="margin-left:4px;background:#6c757d">Download SDK</a>
```
new:
```
<a href="{{ sdk_download_url }}" class="btn btn-sm" style="margin-left:4px;background:#4c566a">Download SDK</a>
```

- [ ] **Step 7: Ticket badge**

old:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none;font-size:13px">#{{ ticket.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff;font-size:13px">{{ ticket.issue }}</span>{% endif %}
```
new:
```
{% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#5e81ac;color:#fff;text-decoration:none;font-size:13px">#{{ ticket.issue }}</a>{% else %}<span class="badge" style="background:#5e81ac;color:#fff;font-size:13px">{{ ticket.issue }}</span>{% endif %}
```

- [ ] **Step 8: Ticket note color**

old:
```
{% if ticket.note %}<span style="margin-left:8px;color:#555">{{ ticket.note }}</span>{% endif %}
```
new:
```
{% if ticket.note %}<span style="margin-left:8px;color:#d8dee9">{{ ticket.note }}</span>{% endif %}
```

- [ ] **Step 9: Remove mark button**

old:
```
<button class="btn btn-sm" style="background:#dc3545;margin-left:12px" onclick="unmarkTicket()">Remove mark</button>
```
new:
```
<button class="btn btn-sm" style="background:#bf616a;margin-left:12px" onclick="unmarkTicket()">Remove mark</button>
```

- [ ] **Step 10: Mark as analyzed button**

old:
```
<button type="submit" id="t-submit" class="btn btn-sm" style="background:#0d6efd">&#10003; Mark as analyzed</button>
```
new:
```
<button type="submit" id="t-submit" class="btn btn-sm" style="background:#5e81ac">&#10003; Mark as analyzed</button>
```

- [ ] **Step 11: SDK not installed banner (no_sdk block)**

old:
```
<div style="padding:16px;background:#fff3cd;border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#9888; SDK <strong>{{ sdk_ver or '' }}</strong> is not installed &mdash; backtrace unavailable.</span>
            {% if sdk_ver %}
            <span id="sdk-install-area"><button class="btn btn-sm" style="background:#fd7e14" onclick="doInstall()">&#8659; Install SDK {{ sdk_ver }}</button></span>
```

NOTE: Use exact file content:

old:
```
        <div style="padding:16px;background:#fff3cd;border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#9888; SDK <strong>{{ sdk_ver or '' }}</strong> is not installed &mdash; backtrace unavailable.</span>
            {% if sdk_ver %}
            <span id="sdk-install-area"><button class="btn btn-sm" style="background:#fd7e14" onclick="doInstall()">&#8659; Install SDK {{ sdk_ver }}</button></span>
```
new:
```
        <div style="padding:16px;background:rgba(235,203,139,0.12);border:1px solid rgba(235,203,139,0.4);border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#9888; SDK <strong>{{ sdk_ver or '' }}</strong> is not installed &mdash; backtrace unavailable.</span>
            {% if sdk_ver %}
            <span id="sdk-install-area"><button class="btn btn-sm" style="background:#ebcb8b;color:#2e3440" onclick="doInstall()">&#8659; Install SDK {{ sdk_ver }}</button></span>
```

- [ ] **Step 12: SDK installed+pending banner (sdk_ready block)**

old:
```
        <div style="padding:16px;background:#d1e7dd;border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#10003; SDK <strong>{{ sdk_ver or '' }}</strong> is installed &mdash; backtrace not yet generated.</span>
            <button id="reprocess-btn" class="btn btn-sm" style="background:#198754;color:#fff" onclick="doReprocess()">&#9654; Process Now</button>
```
new:
```
        <div style="padding:16px;background:rgba(163,190,140,0.12);border:1px solid rgba(163,190,140,0.4);border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#10003; SDK <strong>{{ sdk_ver or '' }}</strong> is installed &mdash; backtrace not yet generated.</span>
            <button id="reprocess-btn" class="btn btn-sm" style="background:#a3be8c;color:#2e3440" onclick="doReprocess()">&#9654; Process Now</button>
```

- [ ] **Step 13: SDK installing banner**

old:
```
        <div style="padding:16px;background:#cfe2ff;border-radius:6px;">
```
new:
```
        <div style="padding:16px;background:rgba(136,192,208,0.12);border:1px solid rgba(136,192,208,0.4);border-radius:6px;">
```

- [ ] **Step 14: SDK not installed (sdk_pending, not sdk_ready) banner + button**

old:
```
        <div style="padding:16px;background:#fff3cd;border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#9888; SDK <strong>{{ sdk_ver or '' }}</strong> is not installed.</span>
            <button id="install-sdk-btn" class="btn btn-sm" style="background:#fd7e14;color:#fff;border:none" onclick="doInstallSdk()">&#11015; Install SDK</button>
```
new:
```
        <div style="padding:16px;background:rgba(235,203,139,0.12);border:1px solid rgba(235,203,139,0.4);border-radius:6px;display:flex;align-items:center;gap:12px;">
            <span>&#9888; SDK <strong>{{ sdk_ver or '' }}</strong> is not installed.</span>
            <button id="install-sdk-btn" class="btn btn-sm" style="background:#ebcb8b;color:#2e3440;border:none" onclick="doInstallSdk()">&#11015; Install SDK</button>
```

- [ ] **Step 15: JS — GH issue prompt span + input border + buttons**

old:
```
            '<span style="font-size:13px;color:#555;margin-right:6px">Issue created? Enter #:</span>'
            + '<input id="gh-auto-issue" type="text" placeholder="e.g. 15884" style="width:90px;font-size:13px;padding:3px 6px;border:1px solid #ccc;border-radius:4px">'
            + ' <button class="btn btn-sm" style="background:#0d6efd" onclick="ghAutoMark()">&#10003; Mark as analyzed</button>'
            + ' <button class="btn btn-sm" style="background:#6c757d"
```
new:
```
            '<span style="font-size:13px;color:#d8dee9;margin-right:6px">Issue created? Enter #:</span>'
            + '<input id="gh-auto-issue" type="text" placeholder="e.g. 15884" style="width:90px;font-size:13px;padding:3px 6px;border:1px solid #4c566a;border-radius:4px">'
            + ' <button class="btn btn-sm" style="background:#5e81ac" onclick="ghAutoMark()">&#10003; Mark as analyzed</button>'
            + ' <button class="btn btn-sm" style="background:#4c566a"
```

- [ ] **Step 16: JS — doInstall: remote not configured badge**

old:
```
"<span class='badge' style='background:#6c757d;color:#fff'>Remote SDK install not configured (set SDK_BASE_URL)</span>"
```

NOTE: Use exact file content (single-quotes inside double-quote string):

old:
```
            "<span class='badge' style='background:#6c757d;color:#fff'>Remote SDK install not configured (set SDK_BASE_URL)</span>"
```
new:
```
            "<span class='badge' style='background:#4c566a;color:#eceff4'>Remote SDK install not configured (set SDK_BASE_URL)</span>"
```

- [ ] **Step 17: JS — doInstall: installing badge + cancel button**

old:
```
                    "<span class='badge' style='background:#fd7e14;color:#fff'>&#9203; Installing…</span>"
                    + " <button class='btn btn-sm' style='background:#dc3545' onclick='doCancel()'>&#10005; Cancel</button>";
```
new:
```
                    "<span class='badge' style='background:#ebcb8b;color:#2e3440'>&#9203; Installing…</span>"
                    + " <button class='btn btn-sm' style='background:#bf616a' onclick='doCancel()'>&#10005; Cancel</button>";
```

- [ ] **Step 18: JS — doInstall: already installed badge**

old:
```
                document.getElementById('sdk-install-area').innerHTML = "<span class='badge' style='background:#198754;color:#fff'>
```

NOTE: Use exact file content:

old:
```
                document.getElementById('sdk-install-area').innerHTML = "<span class='badge' style='background:#198754;color:#fff'>&#10003; Installed — re-run collector to generate backtrace</span>";
```
new:
```
                document.getElementById('sdk-install-area').innerHTML = "<span class='badge' style='background:#a3be8c;color:#2e3440'>&#10003; Installed — re-run collector to generate backtrace</span>";
```

NOTE: The Edit tool is not blocked by the security hook for modifying existing files — only the Write tool triggers it. Use Edit freely.

- [ ] **Step 19: JS — doCancel: cancelled badge + retry button**

old:
```
            "<span class='badge' style='background:#6c757d;color:#fff'>&#10005; Cancelled &mdash; </span>"
            + " <button class='btn btn-sm' style='background:#fd7e14' onclick='doInstall()'>&#8659; Retry Install {{ sdk_ver }}</button>";
```
new:
```
            "<span class='badge' style='background:#4c566a;color:#eceff4'>&#10005; Cancelled &mdash; </span>"
            + " <button class='btn btn-sm' style='background:#ebcb8b;color:#2e3440' onclick='doInstall()'>&#8659; Retry Install {{ sdk_ver }}</button>";
```

- [ ] **Step 20: Verify no old palette colors remain**

```bash
grep -n "#fff3cd\|#d1e7dd\|#cfe2ff\|#fd7e14\|#198754\|#dc3545\|#0d6efd\|#6c757d\|#f6f8fa\|#d0d7de\|#656d76\|color:#555\b" \
    web/templates/cores.html web/templates/core_detail.html
```

Expected: no output. Fix any remaining lines before committing.

- [ ] **Step 21: Commit**

```bash
git add web/templates/cores.html web/templates/core_detail.html
git commit -m "style: apply Nord palette to cores.html and core_detail.html"
```

---

### Task 4: Update analyze.html inline styles

**Files:**
- Modify: `web/templates/analyze.html`

- [ ] **Step 1: Verify old colors present**

```bash
grep -c "#f6f8fa\|#d0d7de\|#0969da\|#656d76\|#dc3545\|#0d6efd\|#6c757d\|#aaa\b\|#666\b\|#555\b\|#e8f4f8\|#f0f0f0" web/templates/analyze.html
```

Expected: number > 0.

- [ ] **Step 2: Loading indicator background + text**

old:
```
    <div id="loading-indicator" style="display: none; margin-top: 16px; padding: 16px; background: #f6f8fa; border-radius: 6px; text-align: center;">
        <span class="spinner"></span>
        <span style="margin-left: 10px; color: #666;">Analyzing crashes... This may take a moment.</span>
```
new:
```
    <div id="loading-indicator" style="display: none; margin-top: 16px; padding: 16px; background: #3b4252; border-radius: 6px; text-align: center;">
        <span class="spinner"></span>
        <span style="margin-left: 10px; color: #d8dee9;">Analyzing crashes... This may take a moment.</span>
```

- [ ] **Step 3: Spinner CSS (inline `<style>` in analyze.html)**

old:
```
        .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid #d0d7de; border-top-color: #0969da; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: middle; }
```
new:
```
        .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid #4c566a; border-top-color: #5e81ac; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: middle; }
```

- [ ] **Step 4: Crashes count muted span**

old:
```
            <span style="color: #656d76; margin-left: 4px;">crashes</span>
```
new:
```
            <span style="color: #d8dee9; margin-left: 4px;">crashes</span>
```

- [ ] **Step 5: Common library badge**

old:
```
            <span style="margin-left: 12px; padding: 2px 8px; background: #e8f4f8; border-radius: 4px; font-size: 12px; color: #2a6496;">
```
new:
```
            <span style="margin-left: 12px; padding: 2px 8px; background: rgba(94,129,172,0.15); border-radius: 4px; font-size: 12px; color: #81a1c1;">
```

- [ ] **Step 6: Processes affected label**

old:
```
        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
```
new:
```
        <div style="font-size: 12px; color: #d8dee9; margin-bottom: 4px;">
```

- [ ] **Step 7: Process name pills**

old:
```
            <span style="background: #f0f0f0; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{{ proc }}</span>
```
new:
```
            <span style="background: #434c5e; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{{ proc }}</span>
```

- [ ] **Step 8: Signature/first/last metadata row (similarity groups)**

old:
```
    <div style="display: flex; gap: 24px; font-size: 12px; color: #656d76; margin-bottom: 8px;">
        <span>Signature: <code>{{ sg.lib_sig[:16] }}</code></span>
```
new:
```
    <div style="display: flex; gap: 24px; font-size: 12px; color: #d8dee9; margin-bottom: 8px;">
        <span>Signature: <code>{{ sg.lib_sig[:16] }}</code></span>
```

- [ ] **Step 9: More-frames footer + no-backtrace text (similarity groups)**

old:
```
    <div style="font-size: 12px; color: #656d76; padding: 4px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
    {% endif %}
    {% else %}
    <p style="font-size: 12px; color: #aaa; margin: 0;">No backtrace available</p>
    {% endif %}
</div>
{% endfor %}

{% elif processes %}
```
new:
```
    <div style="font-size: 12px; color: #d8dee9; padding: 4px 10px; background: #3b4252; border-top: 1px solid #4c566a;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
    {% endif %}
    {% else %}
    <p style="font-size: 12px; color: #6c7a8a; margin: 0;">No backtrace available</p>
    {% endif %}
</div>
{% endfor %}

{% elif processes %}
```

- [ ] **Step 10: Process header muted stats span**

old:
```
        <span style="font-size: 13px; font-weight: normal; color: #656d76; margin-left: 8px;">
```
new:
```
        <span style="font-size: 13px; font-weight: normal; color: #d8dee9; margin-left: 8px;">
```

- [ ] **Step 11: Group card border**

old:
```
        <div style="border: 1px solid #d0d7de; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
```
new:
```
        <div style="border: 1px solid #4c566a; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
```

- [ ] **Step 12: Occurrences muted count span**

old:
```
                    <span style="color: #656d76; font-size: 13px; margin-left: 4px;">{% if g.is_watchdog %}watchdog kill
```
new:
```
                    <span style="color: #d8dee9; font-size: 13px; margin-left: 4px;">{% if g.is_watchdog %}watchdog kill
```

- [ ] **Step 13: Systematic badge (process groups)**

old:
```
                    {% if g.is_systematic %}<span class="badge" style="background:#dc3545;color:#fff;margin-left:6px" title="Same crash signature seen on multiple devices">&#9888; Systematic</span>{% endif %}
```
new:
```
                    {% if g.is_systematic %}<span class="badge" style="background:#bf616a;color:#fff;margin-left:6px" title="Same crash signature seen on multiple devices">&#9888; Systematic</span>{% endif %}
```

- [ ] **Step 14: Ticket badge + unmark/mark buttons (process groups)**

old:
```
                        {% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none;margin-left:6px">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff;margin-left:6px">{{ t.issue }}</span>{% endif %}
                        <button class="btn btn-sm" style="background:#dc3545;margin-left:4px;font-size:11px" onclick="unmarkTicketA(this,'{{ tkey }}')">&#10005;</button>
                    {% elif tkey %}
                        <span id="ta-{{ tkey[:12] }}"><button class="btn btn-sm" style="background:#6c757d;margin-left:6px;font-size:11px" onclick="openTicketA(this,'{{ tkey }}')">+ Mark</button></span>
```

NOTE: Use exact file content:

old:
```
                        {% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none;margin-left:6px">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff;margin-left:6px">{{ t.issue }}</span>{% endif %}
                        <button class="btn btn-sm" style="background:#dc3545;margin-left:4px;font-size:11px" onclick="unmarkTicketA(this,'{{ tkey }}')">&#10005;</button>
                    {% elif tkey %}
                        <span id="ta-{{ tkey[:12] }}"><button class="btn btn-sm" style="background:#6c757d;margin-left:6px;font-size:11px" onclick="openTicketA(this,'{{ tkey }}')">+ Mark</button></span>
```

Hmm, the file content uses actual Jinja braces. Here is the exact old_string to use (copy from the file):

```
                        {% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#0d6efd;color:#fff;text-decoration:none;margin-left:6px">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#0d6efd;color:#fff;margin-left:6px">{{ t.issue }}</span>{% endif %}
                        <button class="btn btn-sm" style="background:#dc3545;margin-left:4px;font-size:11px" onclick="unmarkTicketA(this,'{{ tkey }}')">&#10005;</button>
                    {% elif tkey %}
                        <span id="ta-{{ tkey[:12] }}"><button class="btn btn-sm" style="background:#6c757d;margin-left:6px;font-size:11px" onclick="openTicketA(this,'{{ tkey }}')">+ Mark</button></span>
```

Actually just read the file directly to get the exact text (lines 147-150), then use it as old_string in the Edit call.

new_string equivalent:

```
                        {% if url %}<a href="{{ url }}" target="_blank" class="badge" style="background:#5e81ac;color:#fff;text-decoration:none;margin-left:6px">#{{ t.issue }}</a>{% else %}<span class="badge" style="background:#5e81ac;color:#fff;margin-left:6px">{{ t.issue }}</span>{% endif %}
                        <button class="btn btn-sm" style="background:#bf616a;margin-left:4px;font-size:11px" onclick="unmarkTicketA(this,'{{ tkey }}')">&#10005;</button>
                    {% elif tkey %}
                        <span id="ta-{{ tkey[:12] }}"><button class="btn btn-sm" style="background:#4c566a;margin-left:6px;font-size:11px" onclick="openTicketA(this,'{{ tkey }}')">+ Mark</button></span>
```

- [ ] **Step 15: View All button area (right side of process group row)**

old:
```
                <div style="font-size: 12px; color: #656d76;">
                    {% if g.is_watchdog %}
                    <a href="{{ url_for('cores'
```

NOTE: Use exact file content (lines 153-155):

old:
```
                <div style="font-size: 12px; color: #656d76;">
                    {% if g.is_watchdog %}
                    <a href="{{ url_for('cores', sw_rev=rev, process=g.proc, signal=g.signal) }}" class="btn btn-sm">View All {{ "{:,}".format(g.cnt) }} Crashes</a>
```
new:
```
                <div style="font-size: 12px; color: #d8dee9;">
                    {% if g.is_watchdog %}
                    <a href="{{ url_for('cores', sw_rev=rev, process=g.proc, signal=g.signal) }}" class="btn btn-sm">View All {{ "{:,}".format(g.cnt) }} Crashes</a>
```

- [ ] **Step 16: Binary/signature/dates row + binary strong color**

old:
```
            <div style="display: flex; gap: 24px; font-size: 12px; color: #656d76; margin-bottom: 8px;">
                <span>Binary: <strong style="color:#555">
```
new:
```
            <div style="display: flex; gap: 24px; font-size: 12px; color: #d8dee9; margin-bottom: 8px;">
                <span>Binary: <strong style="color:#eceff4">
```

- [ ] **Step 17: Watchdog description text**

old:
```
            <p style="font-size: 12px; color: #656d76; margin: 0;">Watchdog-initiated (SIGXCPU) — backtraces are not meaningful; all occurrences are grouped together.</p>
```
new:
```
            <p style="font-size: 12px; color: #d8dee9; margin: 0;">Watchdog-initiated (SIGXCPU) — backtraces are not meaningful; all occurrences are grouped together.</p>
```

- [ ] **Step 18: More-frames footer + no-backtrace (process groups)**

old:
```
            <div style="font-size: 12px; color: #656d76; padding: 4px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
            {% endif %}
            {% else %}
            <p style="font-size: 12px; color: #aaa; margin: 0;">No backtrace available</p>
```
new:
```
            <div style="font-size: 12px; color: #d8dee9; padding: 4px 10px; background: #3b4252; border-top: 1px solid #4c566a;">[{{ total - shown }} more frame{{ "s" if total - shown != 1 }}]</div>
            {% endif %}
            {% else %}
            <p style="font-size: 12px; color: #6c7a8a; margin: 0;">No backtrace available</p>
```

- [ ] **Step 19: JS — cancel button in openTicketA**

old:
```
        + ' <button class="btn btn-sm" style="background:#6c757d;font-size:11px" onclick="location.reload()">&#10005;</button>';
    document.getElementById('ta-i-'+btCsum).focus();
```

NOTE: Use exact file content:

old:
```
        + ' <button class="btn btn-sm" style="background:#6c757d;font-size:11px" onclick="location.reload()">&#10005;</button>';
    document.getElementById('ta-i-'+btCsum).focus();
```
new:
```
        + ' <button class="btn btn-sm" style="background:#4c566a;font-size:11px" onclick="location.reload()">&#10005;</button>';
    document.getElementById('ta-i-'+btCsum).focus();
```

- [ ] **Step 20: Verify no old palette colors remain**

```bash
grep -n "#f6f8fa\|#d0d7de\|#0969da\|#656d76\|#dc3545\|#0d6efd\|#6c757d\|#e8f4f8\|#f0f0f0\|#2a6496\|color:#aaa\b\|color:#666\b\|color:#555\b" web/templates/analyze.html
```

Expected: no output. Fix any remaining instances.

- [ ] **Step 21: Commit**

```bash
git add web/templates/analyze.html
git commit -m "style: apply Nord palette to analyze.html"
```

---

## Spec Coverage Checklist

- base.html: all CSS tokens replaced (canvas, surface, border, text, muted, accent, nav, buttons, inputs, error, pagination, pre/code, tabs, stat cards)
- dashboard.html: all inline styles + JS color strings covered (24 changes)
- cores.html: filter card, sig banner, ticket row, badge, JS cancel button
- core_detail.html: all SDK banners, ticket badge, mark buttons, JS string colors
- analyze.html: spinner, loading, process/lib badges, group cards, more-frames, metadata text

**Semantic badges NOT changed (intentional):**
- Signal badges: `signal-4`, `signal-6`, etc. — preserved in base.html
- Cause badge: `{{ b.cause.color }}` / `{{ g.cause.color }}` — Python-generated, not template
- Systematic badge: updated to `#bf616a` (Aurora red) — preserves critical visual meaning
