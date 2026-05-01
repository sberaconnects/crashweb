#!/bin/bash
# Auto-install an SDK from a remote artifact server.
# Triggered by cron or on container start.
#
# Required env vars (set in docker-compose or .env):
#   SDK_BASE_URL      — base URL of artifact server, e.g. https://artifacts.example.com/sdks
#   SDK_PACKAGE_NAME  — package name prefix, e.g. my-device-sdk
#   SDK_VERSION       — version to install, e.g. v1.2.3
#
# Optional env vars:
#   SDK_DIR           — where to install SDKs (default: /var/www/sdks)
#   SDK_SYSROOT_SUBPATH — subdir that marks a successful install (default: empty = dir itself)
#
# No-op if any of SDK_BASE_URL, SDK_PACKAGE_NAME, SDK_VERSION are unset.

set -euo pipefail

SDK_DIR="${SDK_DIR:-/var/www/sdks}"
SDK_BASE_URL="${SDK_BASE_URL:-}"
SDK_PACKAGE_NAME="${SDK_PACKAGE_NAME:-}"
SDK_VERSION="${SDK_VERSION:-}"
SDK_SYSROOT_SUBPATH="${SDK_SYSROOT_SUBPATH:-}"
AUTO_LOG="${SDK_DIR}/.auto-install.log"

LOCK=""
cleanup() { [[ -n "$LOCK" && -f "$LOCK" ]] && rm -f "$LOCK"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$AUTO_LOG"; }

mkdir -p "$SDK_DIR"

if [[ -z "$SDK_BASE_URL" || -z "$SDK_PACKAGE_NAME" || -z "$SDK_VERSION" ]]; then
    log "SDK_BASE_URL, SDK_PACKAGE_NAME, or SDK_VERSION not configured. Skipping auto-install."
    exit 0
fi

VERSION="$SDK_VERSION"
SDK_VDIR="${SDK_DIR}/${VERSION}"
LOCK="${SDK_VDIR}/.installing"
INSTALL_LOG="${SDK_VDIR}/.install.log"

if [[ -n "$SDK_SYSROOT_SUBPATH" ]]; then
    INSTALLED_MARKER="${SDK_VDIR}/${SDK_SYSROOT_SUBPATH}"
else
    INSTALLED_MARKER="${SDK_VDIR}"
fi

log "Checking SDK ${VERSION}..."

if [[ -d "$INSTALLED_MARKER" && ! -f "$LOCK" ]]; then
    log "SDK ${VERSION} already installed. Nothing to do."
    exit 0
fi

if [[ -f "$LOCK" ]]; then
    log "Install already in progress. Nothing to do."
    exit 0
fi

log "Starting install of ${VERSION}..."
mkdir -p "$SDK_VDIR"
touch "$LOCK"

URL="${SDK_BASE_URL}/${SDK_PACKAGE_NAME}-${VERSION}.tar.gz"

CONTENT_LENGTH=$(curl -fsSI "$URL" 2>/dev/null | awk 'tolower($1)=="content-length:" {print $2+0}') || true
CALC=$(( ${CONTENT_LENGTH:-0} > 0 ? CONTENT_LENGTH * 8 : 30 * 1024 * 1024 * 1024 ))
MIN=$(( 30 * 1024 * 1024 * 1024 ))
NEEDED=$(( CALC > MIN ? CALC : MIN ))
log "Space needed: $(( NEEDED / 1024 / 1024 / 1024 )) GB"
python3 /app/sdk_space.py evict "$NEEDED" "$VERSION" "$SDK_DIR" >> "$AUTO_LOG" 2>&1 || \
    log "WARNING: not enough space after eviction; download may fail."

echo "Downloading ${URL} ..." >> "$INSTALL_LOG"
if curl -fsSL --retry 3 --retry-delay 5 "$URL" | tar xz -C "$SDK_VDIR" >> "$INSTALL_LOG" 2>&1; then
    SH_FILE=$(ls "$SDK_VDIR"/*.sh 2>/dev/null | head -1) || true
    if [[ -n "$SH_FILE" ]]; then
        echo "Running SDK installer: $SH_FILE ..." >> "$INSTALL_LOG"
        bash "$SH_FILE" -y -d "$SDK_VDIR" >> "$INSTALL_LOG" 2>&1 || true
        rm -f "$SH_FILE"
    fi
    echo "Done." >> "$INSTALL_LOG"
    rm -f "$LOCK"
    log "Install of ${VERSION} completed successfully."
else
    echo "FAILED" >> "$INSTALL_LOG"
    rm -f "$LOCK"
    log "ERROR: Install of ${VERSION} FAILED. See ${INSTALL_LOG}"
    exit 1
fi
