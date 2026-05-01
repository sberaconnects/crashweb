"""Shared backtrace normalisation and signature utilities.

Used by both the collector service (cs.py) and the web app (app.py) so that
the hash computed at ingest time and the hash recomputed at query time are
always identical.  Any change to normalisation or abort-frame detection must
be made here only.
"""
import hashlib
import re

# Frames that represent abort/panic plumbing rather than the actual fault
# site.  When they appear at the top of a backtrace we strip them so that
# crashes sharing the same abort path still group by their real caller.
_ABORT_FRAME_PATTERNS = [
    r'__pthread_kill_implementation\b',
    r'__pthread_kill_internal\b',
    r'\b__GI_raise\b',
    r'\braise\s*\(',
    r'\b__GI_abort\b',
    r'\babort\s*\(',
    r'\bstd::abort\b',
    r'\b__GI___assert_fail\b',
    r'\b__assert_fail\b',
    r'\bstd::terminate\b',
    r'\b__cxxabiv1::__terminate\b',
    r'\b__cxa_throw\b',
    r'\brust_panic\b',
    r'\brust_begin_unwind\b',
    r'\bcore::panicking::',
    r'\bstd::panicking::',
]
_ABORT_FRAME_RE = re.compile("|".join(_ABORT_FRAME_PATTERNS))


def _normalize_bt_line(line):
    """Strip addresses and variable values to get a stable crash signature."""
    line = re.sub(r'0x[0-9a-fA-F]+', '0x...', line)
    line = re.sub(r'<[^>]*>', '<...>', line)
    line = re.sub(r'=\d+', '=N', line)
    return line.strip()


def _is_abort_frame(line):
    return bool(_ABORT_FRAME_RE.search(line))


def _strip_leading_abort_frames(frames):
    """Drop abort/panic plumbing from the top of the stack.

    Stops at the first frame that is not part of the abort chain so we only
    skip the leading noise, not any later occurrences.
    """
    for i, f in enumerate(frames):
        if not _is_abort_frame(f):
            return frames[i:]
    return frames


def _bt_signature(lines, max_frames=8):
    """Compute a stable MD5 hash from the top N normalized backtrace frames."""
    frames = [l for l in lines if re.match(r'\s*#\d+', l)]
    frames = _strip_leading_abort_frames(frames)
    normalized = "\n".join(_normalize_bt_line(l) for l in frames[:max_frames])
    return hashlib.md5(normalized.encode()).hexdigest()


def _sdk_build(build: str) -> str:
    """Normalize a full build version to the x.y.z SDK directory name.

    '1.20.2-vnv.207'  -> '1.20.2'
    '1.20.2+dev.207'  -> '1.20.2'
    '1.19.0-prod.203' -> '1.19.0'
    """
    m = re.search(r'(\d+\.\d+\.\d+)', build)
    return m.group(1) if m else build
