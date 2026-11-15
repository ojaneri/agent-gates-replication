import string


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _check_raw(member: str) -> None:
    if "\x00" in member:
        raise UnsafePathError("NUL in member name")
    if member.startswith(("/", "\\")):
        raise UnsafePathError("absolute path")
    if len(member) >= 2 and member[0] in string.ascii_letters and member[1] == ":":
        raise UnsafePathError("drive prefix")


def _normalise(member: str) -> str:
    parts: list[str] = []
    for seg in member.replace("\\", "/").split("/"):
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
        _check_raw(member)
        norm = _normalise(member)
        if member.endswith(("/", "\\")):
            continue
        key = norm.lower()
        if key in seen:
            raise UnsafePathError("duplicate target: " + norm)
        seen.add(key)
        result.append(base + "/" + norm)
    return result
