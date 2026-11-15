class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _check_raw(name: str) -> None:
    if "\0" in name:
        raise UnsafePathError("NUL in member name")
    if name.startswith(("/", "\\")):
        raise UnsafePathError("absolute path")
    if len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha():
        raise UnsafePathError("drive prefix")


def _normalise(name: str) -> str:
    _check_raw(name)
    parts: list[str] = []
    for seg in name.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise UnsafePathError("path escapes destination")
            parts.pop()
        else:
            parts.append(seg)
    if not parts:
        raise UnsafePathError("empty path")
    return "/".join(parts)


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    seen: set[str] = set()
    result: list[str] = []
    for member in members:
        norm = _normalise(member)
        if member.endswith(("/", "\\")):
            continue
        key = norm.lower()
        if key in seen:
            raise UnsafePathError("duplicate target: " + norm)
        seen.add(key)
        result.append(base + "/" + norm)
    return result
