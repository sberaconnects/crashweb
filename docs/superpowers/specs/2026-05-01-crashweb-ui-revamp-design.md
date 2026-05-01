# CrashWeb UI Revamp — Design Spec

**Date:** 2026-05-01
**Approach:** CSS-only overhaul — rewrite `base.html` inline styles + targeted per-template tweaks. All Jinja logic stays untouched. No new dependencies, no static file extraction, no framework.

---

## Goals

- Replace the current custom navy/blue UI with a GitHub-style near-monochrome slate developer tool aesthetic
- Rename app from "Coredump Browser" to "CrashWeb" throughout
- Rename nav items for brevity
- Add SVG logo mark and pill-style active nav state
- Keep all semantic badge colors (signal, cause, systematic) — they carry critical meaning

---

## Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `bg-canvas` | `#f6f8fa` | Page background |
| `bg-default` | `#ffffff` | Cards, surfaces |
| `bg-subtle` | `#f6f8fa` | Table headers, filter bar bg |
| `border` | `#d0d7de` | All borders — cards, tables, inputs |
| `fg-default` | `#1f2328` | Body text |
| `fg-muted` | `#656d76` | Secondary labels, meta, stat icons |
| `fg-link` | `#0969da` | Links, active tab underline, active pagination |
| `nav-bg` | `#24292f` | Top bar background |
| `nav-pill` | `#373e47` | Active nav item pill background |
| `btn-primary-bg` | `#1f2328` | Primary buttons |
| `btn-primary-hover` | `#32383f` | Primary button hover |
| `warning-subtle-bg` | `#fff8c5` | Signature filter active banner |
| `warning-subtle-border` | `#d4a72c` | Signature filter active banner border |
| `code-bg` | `#161b22` | Pre/code block background |
| `code-fg` | `#e6edf3` | Pre/code block text |

Signal, cause, and systematic badge colors are **unchanged** — these are semantic and must remain visually distinct.

---

## Typography

- **Body font:** `-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif`
- **Monospace:** `"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`
- **Base size:** 14px
- **Table headers:** 11px, uppercase, `letter-spacing: 0.5px`, `color: #656d76`

---

## Top Nav

### Branding
- Remove emoji `🐛`
- Brand text: `CrashWeb` — weight 600, white, preceded by a small inline SVG logo mark (stylized crash/core symbol, monochrome white, ~18px)
- `<title>` pattern: `Dashboard · CrashWeb`, `Cores · CrashWeb`, etc.

### Nav items (renamed)

| Old label | New label |
|-----------|-----------|
| Coredump Browser | CrashWeb |
| Coredumps | Cores |
| SW Revisions | Revisions |
| Analyze | Analysis |
| Dashboard, Devices | unchanged |

### Active state
- Active link: white text + filled pill background `#373e47`, `border-radius: 6px`, padding `6px 12px`
- Hover (inactive): `color: #fff`, no background — subtle opacity lift

---

## Cards

- Remove `box-shadow` — replaced by `1px solid #d0d7de` border
- `border-radius: 6px`
- Card `h2`: add `border-bottom: 1px solid #d0d7de`, `padding-bottom: 12px`, `margin-bottom: 16px`
- Stat cards: hover = `background: #f6f8fa` + `border-color: #57606a`. No transform, no shadow animation.
- Stat cards: add small inline SVG icon per card (cores = layers icon, devices = cpu/chip icon, revisions = tag icon) — `color: #656d76`

---

## Tables

- Wrap table in element with `border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden`
- `th`: `background: #f6f8fa`, `color: #656d76`, `font-size: 11px`, uppercase, `letter-spacing: 0.5px`
- Row divider: `border-bottom: 1px solid #d0d7de`
- Row hover: `background: #f6f8fa`
- Sticky header preserved

---

## Buttons

| Type | Background | Border | Text | Hover |
|------|-----------|--------|------|-------|
| Primary | `#1f2328` | `rgba(0,0,0,0.15)` | `#fff` | `#32383f` |
| Secondary/ghost | `#f6f8fa` | `#d0d7de` | `#1f2328` | `#eaeef2` |
| Danger | `#dc3545` | — | `#fff` | `#b02a37` |

All buttons: `border-radius: 6px`, `font-size: 13px`.

---

## Inputs & Selects

- `border: 1px solid #d0d7de`
- `border-radius: 6px`
- `background: #ffffff`
- Focus: `outline: 2px solid #0969da; outline-offset: 0`

---

## Pagination

- GitHub-style bordered buttons: `border: 1px solid #d0d7de`, `border-radius: 6px`
- Active page: `background: #0969da; color: #fff; border-color: #0969da`
- Hover: `background: #f6f8fa`

---

## Pre / Code Blocks

- Background: `#161b22`
- Text: `#e6edf3`
- Copy button: ghost style on dark bg — `background: rgba(255,255,255,0.08)`, `border: 1px solid rgba(255,255,255,0.15)`, `color: #e6edf3`
- Copy button copied state: `background: #238636` (GitHub green)

---

## Page-Specific

### Filter Bar (Cores, Revisions, Devices)
- Wrapped in a card with `background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px`
- Visually separated from the data table below

### Signature Filter Banner (Cores)
- `background: #fff8c5; border: 1px solid #d4a72c; border-radius: 6px; padding: 10px 14px`

### Core Detail — Tabs
- Default: `border-bottom: 2px solid transparent; color: #656d76`
- Active: `border-bottom: 2px solid #0969da; color: #1f2328`
- Hover: `color: #1f2328`

### Breadcrumbs
- Separator: `›` in `#656d76`
- Links: `#0969da`
- Current page: `#1f2328`, no underline

### Dashboard SDK Card
- Header separator border applied
- Autolog toggle: ghost secondary button style

---

## Files Changed

| File | Change |
|------|--------|
| `web/templates/base.html` | Full CSS rewrite + nav HTML (brand, renamed links, SVG icon, pill active) |
| `web/templates/dashboard.html` | Stat card icons, title update |
| `web/templates/cores.html` | Filter bar card wrapper, title update |
| `web/templates/core_detail.html` | Tab styles (inline), title update |
| `web/templates/revisions.html` | Filter bar card wrapper, title update |
| `web/templates/devices.html` | Title update |
| `web/templates/device_detail.html` | Title update |
| `web/templates/analyze.html` | Title update |
| `web/templates/error.html` | Title update |

No Python changes. No new files. No structural changes to any template.

---

## What Does NOT Change

- All Jinja template logic
- Signal badge colors (SIGSEGV red, SIGABRT yellow, etc.)
- Cause badge colors (Watchdog, OOM, Stack Smash, etc.)
- Systematic badge (red warning)
- SDK install JS logic
- Ticket/GitHub issue JS logic
- All route URLs and form actions
