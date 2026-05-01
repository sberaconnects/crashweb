#!/bin/bash
# Auto-install the latest SDK from Artifactory.
# Runs at @reboot and 00:00 daily via cron.
# No-op if latest is already installed or an install is already in progress.

set -euo pipefail

SDK_DIR="/var/www/sdks"
AUTO_LOG="${SDK_DIR}/.auto-install.log"
ART_LIST_API="https://artifactory-ehv.ta.philips.com/artifactory/api/storage/synergy-generic-rnd/sdk/philips-imx8mp-delta-transport/release"
ART_BASE="https://artifactory-ehv.ta.philips.com/artifactory/synergy-generic-rnd/sdk/philips-imx8mp-delta-transport/release"
SYSROOT_SUBPATH="sysroots/cortexa53-crypto-mgl-linux"

# Cleanup lock file on exit (covers both success and unexpected failure)
LOCK=""
cleanup() { [[ -n "$LOCK" && -f "$LOCK" ]] && rm -f "$LOCK"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$AUTO_LOG"; }

mkdir -p "$SDK_DIR"

# Resolve latest available version from Artifactory
CRED_ARG=()
if [[ -n "${ARTIFACTORY_USER:-}" && -n "${ARTIFACTORY_PASS:-}" ]]; then
    CRED_ARG=(-u "${ARTIFACTORY_USER}:${ARTIFACTORY_PASS}")
fi

log "Checking latest SDK version from Artifactory..."
LIST_JSON=$(curl -fsSL "${CRED_ARG[@]}" "${ART_LIST_API}?list&deep=0&listFolders=0" 2>>"$AUTO_LOG") || {
    log "ERROR: Failed to reach Artifactory"
    exit 1
}

# Extract latest: sort by version+run descending, take first
LATEST=$(echo "$LIST_JSON" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
files = data.get('files', [])
entries = []
for f in files:
    m = re.search(r'sdk-philips-imx8mp-delta-transport-(\d+\.\d+\.\d+)\+dev\.(\d+)\.tar\.gz$', f['uri'])
    if m:
        ver = tuple(int(x) for x in m.group(1).split('.'))
        run = int(m.group(2))
        entries.append((ver, run, m.group(1), m.group(2)))
if not entries:
    print('')
else:
    entries.sort(reverse=True)
    best = entries[0]
    print(f'v{best[2]} {best[2]}+dev.{best[3]}')
") 2>>"$AUTO_LOG"

if [[ -z "$LATEST" ]]; then
    log "ERROR: Could not determine latest version"
    exit 1
fi

VERSION=$(echo "$LATEST" | cut -d' ' -f1)
ART_VERSION=$(echo "$LATEST" | cut -d' ' -f2)
SDK_VDIR="${SDK_DIR}/${VERSION}"
SYSROOT="${SDK_VDIR}/${SYSROOT_SUBPATH}"
LOCK="${SDK_VDIR}/.installing"
INSTALL_LOG="${SDK_VDIR}/.install.log"

log "Latest version: ${VERSION} (${ART_VERSION})"

# No-op checks
if [[ -d "$SYSROOT" ]]; then
    log "Already installed. Nothing to do."
    exit 0
fi
if [[ -f "$LOCK" ]]; then
    log "Install already in progress. Nothing to do."
    exit 0
fi

log "Starting install of ${VERSION}..."
mkdir -p "$SDK_VDIR"
touch "$LOCK"
URL="${ART_BASE}/sdk-philips-imx8mp-delta-transport-${ART_VERSION}.tar.gz"

# Check available disk space; evict oldest SDKs if needed.
# Probe Content-Length via HEAD; fall back to 30 GB if unavailable.
# Use || true so a HEAD failure (network blip) never aborts the install.
CONTENT_LENGTH=$(curl -fsSI "${CRED_ARG[@]}" "$URL" 2>/dev/null | awk 'tolower($1)=="content-length:" {print $2+0}') || true
CALC=$(( ${CONTENT_LENGTH:-0} > 0 ? CONTENT_LENGTH * 8 : 30 * 1024 * 1024 * 1024 ))
MIN=$(( 30 * 1024 * 1024 * 1024 ))
NEEDED=$(( CALC > MIN ? CALC : MIN ))
log "Space needed: $(( NEEDED / 1024 / 1024 / 1024 )) GB (Content-Length=${CONTENT_LENGTH:-unknown})"
python3 /app/sdk_space.py evict "$NEEDED" "$VERSION" "$SDK_DIR" >> "$AUTO_LOG" 2>&1 || \
    log "WARNING: not enough space after eviction; download may fail."

echo "Downloading ${URL} ..." >> "$INSTALL_LOG"
if curl -fsSL --retry 3 --retry-delay 5 "${CRED_ARG[@]}" "$URL" | tar xz -C "$SDK_VDIR" >> "$INSTALL_LOG" 2>&1; then
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
