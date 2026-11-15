class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _normalise(member: str) -> list[str]:
    if "\x00" in member:
        raise UnsafePathError("NUL in member name")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError("absolute path")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError("drive prefix")
    parts: list[str] = []
    for seg in member.replace("\\", "/").split("/"):
        if seg == "" or seg == ".":
            continue
        if seg == "..":
            if not parts:
                raise UnsafePathError("path escapes destination")
            parts.pop()
        else:
            parts.append(seg)
    if not parts:
        raise UnsafePathError("empty path")
    return parts


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    result: list[str] = []
    seen: set[str] = set()
    for member in members:
        parts = _normalise(member)
        if member[-1] in ("/", "\\"):
            continue
        rel = "/".join(parts)
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError("duplicate path: " + rel)
        seen.add(key)
        result.append(base + "/" + rel)
    return result
