import re
import string

_SEPARATORS = re.compile(r"[/\\]")
_DRIVE_LETTERS = frozenset(string.ascii_letters)


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _check_dest(dest):
    """Validate dest and return it without trailing slashes."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")
    return dest.rstrip("/")


def _is_drive(name):
    """True if name starts with a Windows drive prefix such as 'C:'."""
    return len(name) >= 2 and name[1] == ":" and name[0] in _DRIVE_LETTERS


def _check_prefix(name):
    """Reject members that are absolute, have a drive prefix, or contain NUL."""
    if "\x00" in name:
        raise UnsafePathError(f"NUL character in member: {name!r}")
    if name[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member: {name!r}")
    if _is_drive(name):
        raise UnsafePathError(f"drive prefix in member: {name!r}")


def _segments(name):
    """Split a member into normalised segments, refusing any climb above the root."""
    segments = []
    for part in _SEPARATORS.split(name):
        if part in ("", "."):
            continue
        if part != "..":
            segments.append(part)
        elif segments:
            segments.pop()
        else:
            raise UnsafePathError(f"member climbs above destination: {name!r}")
    return segments


def _normalise(name):
    """Return (segments, is_dir) for one member, or raise UnsafePathError."""
    _check_prefix(name)
    segments = _segments(name)
    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {name!r}")
    return segments, name.endswith(("/", "\\"))


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    base = _check_dest(dest)
    targets = []
    seen = set()
    for name in members:
        segments, is_dir = _normalise(name)
        if is_dir:
            continue
        rel = "/".join(segments)
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate member: {name!r}")
        seen.add(key)
        targets.append(f"{base}/{rel}")
    return targets
