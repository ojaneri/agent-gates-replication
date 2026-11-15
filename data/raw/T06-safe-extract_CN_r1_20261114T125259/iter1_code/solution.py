class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _normalise(member: str) -> list:
    if "\0" in member:
        raise UnsafePathError("NUL in member name")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError("absolute path")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError("drive prefix")
    out = []
    for seg in member.replace("\\", "/").split("/"):
        if seg == "" or seg == ".":
            continue
        if seg == "..":
            if not out:
                raise UnsafePathError("path escapes destination")
            out.pop()
        else:
            out.append(seg)
    if not out:
        raise UnsafePathError("empty path")
    return out


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    result = []
    seen = set()
    for m in members:
        parts = _normalise(m)
        if m[-1:] in ("/", "\\"):
            continue
        path = "/".join(parts)
        key = path.lower()
        if key in seen:
            raise UnsafePathError("duplicate target: " + path)
        seen.add(key)
        result.append(base + "/" + path)
    return result
