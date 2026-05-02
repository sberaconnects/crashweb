# CrashWeb Nord Theme — Design Spec

**Date:** 2026-05-01
**Approach:** CSS-only color swap — replace GitHub slate palette with Nord palette across `base.html` and per-template inline styles. No structural HTML changes. No new dependencies.

---

## Color Palette

### Nord Reference

| Nord name | Value | Notes |
|-----------|-------|-------|
| Polar Night 0 | `#2e3440` | Page canvas |
| Polar Night 1 | `#3b4252` | Card/surface |
| Polar Night 2 | `#434c5e` | Subtle surface / hover |
| Polar Night 3 | `#4c566a` | Borders, ghost button bg |
| Snow Storm 0 | `#d8dee9` | Muted text |
| Snow Storm 1 | `#e5e9f0` | Secondary text |
| Snow Storm 2 | `#eceff4` | Body text (primary) |
| Frost 0 | `#8fbcbb` | Cyan (unused) |
| Frost 1 | `#88c0d0` | Ice blue (info banners) |
| Frost 2 | `#81a1c1` | Accent hover / light blue |
| Frost 3 | `#5e81ac` | Primary accent (links, buttons, active) |
| Aurora red | `#bf616a` | Error, danger, SIGABRT badge-compatible |
| Aurora orange | `#d08770` | Warning (unused) |
| Aurora yellow | `#ebcb8b` | Warning banners, install button |
| Aurora green | `#a3be8c` | Success states, copy-done |
| Aurora purple | `#b48ead` | (unused) |

### Token Mapping

| Token | Old value | New value |
|-------|-----------|-----------|
| bg-canvas | `#f6f8fa` | `#2e3440` |
| bg-surface | `#ffffff` | `#3b4252` |
| bg-subtle | `#f6f8fa` (inline) | `#434c5e` |
| border | `#d0d7de` | `#4c566a` |
| fg-default | `#1f2328` | `#eceff4` |
| fg-muted | `#656d76` | `#d8dee9` |
| fg-link / accent | `#0969da` | `#5e81ac` |
| nav-bg | `#24292f` | `#242933` |
| nav-pill | `#373e47` | `#4c566a` |
| btn-primary-bg | `#1f2328` | `#5e81ac` |
| btn-primary-hover | `#32383f` | `#81a1c1` |
| btn-ghost-bg | `#f6f8fa` | `#434c5e` |
| btn-ghost-hover | `#eaeef2` | `#4c566a` |
| btn-danger-bg | `#dc3545` | `#bf616a` |
| btn-danger-hover | `#b02a37` | `#a0505a` |
| stat-card-hover-border | `#57606a` | `#81a1c1` |
| error-bg | `#ffebe9` | `rgba(191,97,106,0.15)` |
| error-border | `rgba(255,129,130,0.4)` | `rgba(191,97,106,0.5)` |
| error-text | `#82071e` | `#bf616a` |
| code-bg | `#161b22` | `#242933` |
| code-fg | `#e6edf3` | `#eceff4` |
| copy-done-bg | `#238636` | `#a3be8c` |
| pagination-active | `#0969da` | `#5e81ac` |
| tab-active-border | `#0969da` | `#5e81ac` |
| focus-outline | `#0969da` | `#5e81ac` |
| ticket-row-bg | `#f6f8fa` (inline) | `#434c5e` |
| sig-banner-bg | `#fff8c5` | `rgba(235,203,139,0.12)` |
| sig-banner-border | `#d4a72c` | `rgba(235,203,139,0.5)` |
| filter-card-bg | `#f6f8fa` (inline) | `#3b4252` |
| sdk-warning-bg | `#fff3cd` | `rgba(235,203,139,0.12)` |
| sdk-success-bg | `#d1e7dd` | `rgba(163,190,140,0.12)` |
| sdk-info-bg | `#cfe2ff` | `rgba(136,192,208,0.12)` |
| sdk-install-btn | `#fd7e14` | `#ebcb8b` (dark text) |
| sdk-process-btn | `#198754` | `#a3be8c` (dark text) |
| badge-blue | `#0d6efd` | `#5e81ac` |
| badge-green | `#198754` | `#a3be8c` |
| badge-red | `#dc3545` | `#bf616a` |
| badge-gray | `#6c757d` | `#4c566a` |
| analyze-spinner-track | `#d0d7de` | `#4c566a` |
| analyze-spinner-head | `#0969da` | `#5e81ac` |
| analyze-proc-badge-bg | `#f0f0f0` | `#434c5e` |
| analyze-device-badge-bg | `#e8f4f8` | `rgba(94,129,172,0.15)` |
| analyze-device-badge-color | `#2a6496` | `#81a1c1` |
| analyze-loading-bg | `#f6f8fa` | `#3b4252` |
| analyze-loading-text | `#666` | `#d8dee9` |
| analyze-no-bt-color | `#aaa` | `#6c7a8a` |

### Semantic badge colors (UNCHANGED)
Signal badges (SIGSEGV, SIGABRT, etc.), cause badges (Watchdog, OOM, Stack Smash), and Systematic badge — all unchanged. These carry critical meaning.

---

## What Changes

| File | Change |
|------|--------|
| `web/templates/base.html` | Full CSS rewrite — all palette tokens replaced |
| `web/templates/dashboard.html` | Inline styles + JS color strings updated |
| `web/templates/cores.html` | Filter card bg, signature banner, ticket row |
| `web/templates/core_detail.html` | SDK banners, ticket badge, mark buttons, inline colors |
| `web/templates/analyze.html` | Spinner, loading bg, process/device badges, inline colors |

Templates `revisions.html`, `devices.html`, `device_detail.html`, `error.html` — no inline color styles, so no changes needed beyond what's already in base.html.

---

## What Does NOT Change

- All Jinja template logic and structure
- Signal badge colors
- Cause badge colors
- Systematic badge color
- Nav HTML structure, SVG logo, link labels
- All route URLs and form actions
- `tools/` scripts
