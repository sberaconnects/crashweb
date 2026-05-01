# crashweb Generalization Design

**Date:** 2026-05-01
**Status:** Approved

## Goal

Extract `synergy-coredump-web` (Philips-internal) into `crashweb` — a generic, public coredump collection and analysis web tool deployable by any developer or organization with Docker.

## Decisions

| Topic | Decision |
|-------|----------|
| Project name | `crashweb` |
| Auth | Stripped entirely (no LDAP, no basic auth) |
| SDK fetch | Local dir default; HTTP fetch enabled via `SDK_BASE_URL` env var |
| GitHub integration | Configurable via `GITHUB_REPO` env var; hidden if unset |
| CI/CD | Generic `ubuntu-latest` workflow template with comments |
| New repo | Public repo under personal GitHub account (`sbera.connects@gmail.com`) |

## Architecture

Stack unchanged: Flask + MariaDB + Traefik + Docker Compose. No feature additions or removals. Pure generalization — remove company coupling, make config-driven.

Services:
- `ccs` — coredump collector (receives dumps from devices)
- `flask-web` — Flask UI (browse, analyze, triage)
- `mariadb` — persistent storage
- `traefik` — reverse proxy + TLS (auth middleware stripped)

## Config / Env Vars

All runtime config flows through `web/config.py` reading from environment.

```python
# web/config.py
import os

DB_HOST          = os.getenv('DB_HOST', 'mariadb')
DB_USER          = os.getenv('DB_USER', 'apache')
DB_PASS          = os.getenv('DB_PASS', '')
DB_NAME          = os.getenv('DB_NAME', 'coredumps')
DB_PORT          = os.getenv('DB_PORT', '3306')

SECRET_KEY       = os.getenv('SECRET_KEY')             # required — no default, fails fast if unset

SDK_DIR          = os.getenv('SDK_DIR', '/home/sdks')
SDK_BASE_URL     = os.getenv('SDK_BASE_URL', '')       # optional — enables HTTP SDK fetch
SDK_PACKAGE_NAME = os.getenv('SDK_PACKAGE_NAME', '')   # optional — tarball name pattern for HTTP fetch

GITHUB_REPO      = os.getenv('GITHUB_REPO', '')        # optional — e.g. "owner/repo"

COREDUMP_DIR     = os.getenv('COREDUMP_DIR', '/home/coredumps')
```

`.env.example` documents every setting with inline comments.

## Files Changed / Deleted / Added

Source: `/home/sbera/git/work/synergy-coredump-web` (original, untouched)
Destination: `/home/sbera/git/personal/crashweb` (new public project)

### Delete (not copied to new repo)
- `.github/philips-repo.yaml`
- `catalog-info.yaml`
- `mkdocs.yaml`
- `docs/index.md`
- `traefik/auth-users-dev`

### Modify
| File | Change |
|------|--------|
| `web/config.py` | Full rewrite — env-var driven, `SECRET_KEY` required |
| `web/app.py` | Replace Artifactory URLs → `SDK_BASE_URL`; GitHub org → `GITHUB_REPO`; remove all hardcoded Philips/Synergy strings |
| `web/templates/core_detail.html` | Conditionally render GitHub issue link only if `GITHUB_REPO` set |
| `web/tests/test_app.py` | Update GitHub URL refs to use `GITHUB_REPO` pattern |
| `traefik/traefik_dynamic-*.yml` | Strip LDAP middleware; replace Philips domains with placeholder hostnames |
| `docker-compose*.yml` | Remove LDAP env vars; add new env vars; replace Philips cert/image refs |
| `README.md` | Full rewrite — generic setup guide, no Philips/Synergy references |
| `CONTRIBUTING.md` | Replace Philips-specific guidelines with generic |
| `.github/workflows/deploy-production.yml` | Replace self-hosted runner with `ubuntu-latest`; add setup comments as deployment template |

### Add
- `.env.example` — documented env var template

### Keep Unchanged
- `docker/shared/bt_utils.py` — pure coredump analysis logic
- `docker/ccs/cs.py` — collector logic (verify no Philips refs before keeping)
- `docker/ccs/sql/01_schema.sql`, `02_indices.sql` — generic schema
- `docker/flask-web/Dockerfile`
- `web/requirements.txt`

## New Repo Setup

1. Work in `/home/sbera/git/personal/crashweb/` (already created)
2. Copy files from original (exclude `.git/` and deleted files above)
3. Apply all modifications
4. `git init` + initial commit
5. `gh repo create crashweb --public` (personal account: `sbera.connects`)
6. Push to `github.com/sbera.connects/crashweb`

## Company Strings Replaced

| Was | Becomes |
|-----|---------|
| `synergy.philips.com` | configurable via env / placeholder in docs |
| `philips-internal/synergy-base` | `${GITHUB_REPO}` |
| `artifactory-ehv.ta.philips.com/...` | `${SDK_BASE_URL}/...` |
| `sdk-philips-imx8mp-delta-transport` | `${SDK_PACKAGE_NAME}` |
| LDAP DN / server / groups | removed |
| IP ranges `10.218.40.0/21` etc. | removed |
| Cert filenames `*_synergy_philips_com.*` | generic names |
| Self-hosted runner `bbl2xgps` | `ubuntu-latest` |
| `synergy-coredump-web` (project name) | `crashweb` |

## Success Criteria

- `docker compose up` works out of the box with only `.env` file configured
- No Philips, Synergy, Artifactory, or internal IP references remain in any file
- README sufficient for a stranger to deploy crashweb in under 30 minutes
- `SECRET_KEY` not set → app refuses to start with clear error
- `GITHUB_REPO` not set → issue link hidden (no broken links)
- `SDK_BASE_URL` not set → local SDK dir still works
