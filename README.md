# crashweb

A self-hosted web UI for collecting, browsing, and analyzing coredumps from embedded Linux devices.

## Features

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Stats, top crashing binaries with cause classification, recent coredumps |
| Coredumps | `/cores` | Filterable list by device, SW revision, signal, binary, backtrace checksum |
| Core detail | `/core/<id>` | Metadata, backtrace, journal, related crashes, ticket marking, GitHub issue creation |
| Devices | `/devices` | All known devices with crash counts |
| Device detail | `/device/<id>` | Per-device coredump list |
| SW Revisions | `/revisions` | All SW revisions with crash counts and SDK install status |
| Crash Analysis | `/analyze` | Crash grouping by backtrace signature — systematic bug detection, cause badges |

Key capabilities:

- **Crash cause classification** — detects Watchdog Timeout, OOM Kill, Stack Smash, Bus Error, Segfault from journal lines
- **Systematic bug detection** — flags crash signatures seen on more than one device
- **Ticket / Mark-as-analyzed** — mark any crash signature with an issue number, propagated across all pages
- **Create GitHub Issue** — pre-fills title and backtrace in GitHub `issues/new` (requires `GITHUB_REPO`)
- **SDK management** — install SDKs per revision for backtrace generation (requires `SDK_BASE_URL`)
- **Coredump download** — direct download of `.core.gz` files with path traversal protection

## Stack

- **Flask** (Python 3) + gunicorn
- **MariaDB 10.6**
- **Traefik 3.6.7** (reverse proxy + TLS)
- **Docker Compose**

## Quick Start (local, no TLS)

```bash
# 1. Clone
git clone https://github.com/sbera.connects/crashweb
cd crashweb

# 2. Configure
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a random string:
#   SECRET_KEY=$(openssl rand -hex 32)

# 3. Start (no Traefik — Flask on port 8080)
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d mariadb flask-web ccs

# 4. Open http://localhost:8080
```

## Production Deployment

```bash
cp .env.example .env
# Fill in SECRET_KEY and any optional settings

# Edit traefik/traefik_dynamic-prod.yml:
#   - Replace YOUR_DOMAIN with your domain name
#   - Set certFile path to your TLS certificate

# Place SSL key at: ~/.ssh/crashweb.key

docker compose -f docker-compose.yml -f docker-compose-production.yml up -d --build
```

## Configuration

All settings via environment variables (or `.env` file). See `.env.example` for full list.

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `SECRET_KEY` | Yes | Flask secret key — any long random string |
| `GITHUB_REPO` | No | `owner/repo` — enables "Create GitHub Issue" button |
| `SDK_BASE_URL` | No | Base URL for SDK downloads — enables remote SDK install |
| `SDK_PACKAGE_NAME` | No | SDK tarball name prefix (e.g. `my-device-sdk`) |
| `SDK_VERSION` | No | Version to auto-install on container start |
| `SDK_SYSROOT_SUBPATH` | No | Subdir inside SDK dir that marks install complete |
| `DB_HOST` | No | MariaDB host (default: `mariadb`) |
| `DB_USER` | No | DB user (default: `apache`) |
| `DB_PASSWORD` | No | DB password (default: empty) |
| `DB_NAME` | No | DB name (default: `coredumps`) |

## Device Setup

Devices send coredumps to the `ccs` service on port 5555. The collector service:

1. Receives the coredump file
2. Stores it to `COREDUMP_DIR` (`/home/coredumps` on the host)
3. Records metadata in MariaDB
4. Triggers backtrace generation (if SDK installed for the SW revision)

## SDK Installation

Backtraces require the matching SDK (cross-compiled sysroot) for the target device SW revision.

**Local:** Place SDKs in `/home/sdks/{version}/` on the host. The version dir must contain a sysroot (or set `SDK_SYSROOT_SUBPATH` appropriately).

**Remote:** Set `SDK_BASE_URL` and `SDK_PACKAGE_NAME`. The app will download `{SDK_BASE_URL}/{SDK_PACKAGE_NAME}-{version}.tar.gz` on demand. If the tarball contains a `.sh` installer, it runs automatically.

## Development

```bash
cp .env.example .env
# Set SECRET_KEY in .env

# Generate local certs (required for TLS in dev)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/localhost.key \
  -out certs/localhost.crt -days 365 -nodes \
  -subj '/CN=coredumps.localhost'

# Add to /etc/hosts: 127.0.0.1 coredumps.localhost

docker compose -f docker-compose.yml -f docker-compose-dev.yml up -d
# Flask hot-reloads on code changes
# UI: https://coredumps.localhost
```

### Running Tests

```bash
cd web
pip install -r requirements.txt
pytest tests/ -v
```

## License

See [LICENSE](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
