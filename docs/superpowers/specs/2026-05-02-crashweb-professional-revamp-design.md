# CrashWeb Professional Revamp — Design Spec

**Date:** 2026-05-02
**Approach:** Full CSS+layout overhaul. Sidebar nav replaces top nav. Tokyo Night palette. Page renames. Better typography and stat cards. No structural Jinja logic changes. No new dependencies.

---

## Color Palette — Tokyo Night

| Token | Value | Role |
|-------|-------|------|
| canvas | `#1a1b26` | Page background |
| surface | `#24283b` | Cards, panels |
| surface-hi | `#2f3354` | Hover state, subtle surface |
| border | `#414868` | All borders |
| fg | `#c0caf5` | Primary text |
| fg-muted | `#565f89` | Secondary / muted text |
| accent | `#7aa2f7` | Links, active nav, buttons, focus |
| accent-hover | `#89b4fa` | Button hover |
| error | `#f7768e` | Danger, error states |
| warning | `#e0af68` | Warning banners, install button |
| success | `#9ece6a` | Success states, copy-done |
| sidebar-bg | `#16161e` | Sidebar background (darker) |
| code-bg | `#16161e` | Code blocks |

---

## Layout: Sidebar Navigation

Replace horizontal `<nav>` with fixed 220px left sidebar `<aside class="sidebar">`.

Sidebar structure:
```
┌─────────────────┐
│ ⚡ CrashWeb     │  ← brand (logo + name)
├─────────────────┤
│ ● Overview      │  ← active: #7aa2f7 text + 3px left accent bar
│   Crashes       │  ← inactive: #565f89
│   Devices       │
│   Firmware      │
│   Patterns      │
├─────────────────┤
│   v<version>    │  ← footer, muted
└─────────────────┘
```

Main content: `margin-left: 220px; padding: 28px 32px`.

---

## Page Renames

| Old | New | Endpoint(s) |
|-----|-----|-------------|
| Dashboard | Overview | `index` |
| Cores | Crashes | `cores`, `core_detail` |
| Revisions | Firmware | `revisions` |
| Analysis | Patterns | `analyze` |
| Devices | Devices | (unchanged) |

Changes needed: `{% block title %}`, `<h1>`, sidebar link labels, stat card labels.

---

## Stat Cards (Overview page)

- Number font-size: 40px
- Colored top accent bar (3px, color per card: accent/warning/success)
- Label: 12px uppercase letter-spaced
- Stat card min-width: 160px

---

## Tables

- Row height: min 44px (via `td { padding: 10px 14px }`)
- Critical rows (SIGSEGV, systematic): 3px left border in error color
- Header: 11px uppercase, fg-muted, bg: surface
- Hover: surface-hi

---

## Typography

- Body: 14px, `Inter, -apple-system, ...` (same stack, just updated)
- Page title (h1): 24px, 700, fg, margin-bottom 20px
- Card title (h2): 14px, 600, uppercase, letter-spacing 0.8px, fg-muted — subtle section header style
- Code/pre: `JetBrains Mono, SFMono-Regular, Consolas, monospace`

---

## What Changes

| File | Changes |
|------|---------|
| `web/templates/base.html` | Full CSS rewrite (Tokyo Night) + sidebar HTML replaces top nav |
| `web/templates/dashboard.html` | `<h1>` → "Overview", stat labels "Crashes"/"Firmware", inline color updates, stat card accent bars |
| `web/templates/cores.html` | `{% block title %}` + `<h1>` → "Crashes", inline color updates |
| `web/templates/core_detail.html` | Inline color updates only |
| `web/templates/revisions.html` | `{% block title %}` + `<h1>` → "Firmware", check inline colors |
| `web/templates/analyze.html` | `{% block title %}` + `<h1>` → "Patterns", inline color updates |
| `web/templates/devices.html` | Check inline colors |
| `web/templates/device_detail.html` | Check inline colors |

---

## What Does NOT Change

- All Jinja template logic, route URLs, form actions
- Signal badge colors (semantic — unchanged)
- Cause badge colors
- Systematic badge color
- All `tools/` scripts
- Nav SVG icon (reused in sidebar brand)
