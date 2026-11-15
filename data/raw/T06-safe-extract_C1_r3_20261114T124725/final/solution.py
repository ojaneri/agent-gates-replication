import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


# Both "/" and "\" separate segments, because Windows-made archives use "\".
_SEPARATORS = re.compile(r"[/\\]")


def _normalise(member: str) -> tuple[str, bool]:
    """Return (normalised relative path, is_directory_entry) or raise."""
    if "\x00" in member:
        raise UnsafePathError(f"NUL character in member {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member {member!r}")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError(f"drive-prefixed member {member!r}")

    stack: list[str] = []
    for segment in _SEPARATORS.split(member):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not stack:
                raise UnsafePathError(f"member {member!r} climbs above destination")
            stack.pop()
        else:
            stack.append(segment)

    if not stack:
        raise UnsafePathError(f"member {member!r} is empty after normalisation")
    is_dir = member[-1:] in ("/", "\\")
    return "/".join(stack), is_dir


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    base = dest.rstrip("/")
    targets: list[str] = []
    seen: set[str] = set()
    for member in members:
        rel, is_dir = _normalise(member)
        if is_dir:
            continue
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError(f"member {member!r} collides with an earlier member")
        seen.add(key)
        targets.append(base + "/" + rel)
    return targets
