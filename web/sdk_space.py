"""SDK disk-space management utilities.

Shared by app.py (imported) and auto-install-sdk.sh (invoked as a subprocess).

CLI usage (for bash callers):
    python3 sdk_space.py evict <needed_bytes> <keep_version> <sdk_dir>

Exit code 0 = enough space available after eviction (or was already enough).
Exit code 1 = not enough space even after evicting everything.
"""
import logging
import os
import shutil
import sys

log = logging.getLogger(__name__)


def evict_sdks_for_space(sdk_dir: str, needed_bytes: int, keep_version: str) -> bool:
    """Remove oldest SDK dirs in sdk_dir until needed_bytes of free space is available.

    sdk_dir       -- directory containing vX.Y.Z SDK subdirs
    needed_bytes  -- estimated bytes required (tarball + extracted)
    keep_version  -- version name being installed; never removed

    Returns True if enough space is (now) available, False otherwise.
    """
    if not os.path.isdir(sdk_dir):
        return True
    free = shutil.disk_usage(sdk_dir).free
    if free >= needed_bytes:
        return True
    candidates = sorted(
        (e for e in os.scandir(sdk_dir)
         if e.is_dir() and e.name != keep_version),
        key=lambda e: e.stat().st_mtime,
    )
    for entry in candidates:
        if free >= needed_bytes:
            break
        log.info('[sdk] Evicting %s to free disk space', entry.name)
        shutil.rmtree(entry.path, ignore_errors=True)
        free = shutil.disk_usage(sdk_dir).free
    if free < needed_bytes:
        log.warning('[sdk] Only %d MB free after eviction; download may fail', free // 1024 ** 2)
        return False
    return True


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] != 'evict':
        print(f'Usage: {sys.argv[0]} evict <needed_bytes> <keep_version> <sdk_dir>', file=sys.stderr)
        sys.exit(2)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    _, _, needed_bytes, keep_version, sdk_dir = sys.argv
    ok = evict_sdks_for_space(sdk_dir, int(needed_bytes), keep_version)
    sys.exit(0 if ok else 1)
