class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _normalise(name: str) -> list[str]:
    if "\x00" in name:
        raise UnsafePathError("NUL in member name")
    if name[:1] in ("/", "\\"):
        raise UnsafePathError("absolute path")
    if len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha():
        raise UnsafePathError("drive prefix")
    out: list[str] = []
    for seg in name.replace("\\", "/").split("/"):
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
    result: list[str] = []
    seen: set[str] = set()
    for m in members:
        parts = _normalise(m)
        if m[-1:] in ("/", "\\"):
            continue
        rel = "/".join(parts)
        key = rel.lower()
        if key in seen:
            raise UnsafePathError("duplicate target: " + rel)
        seen.add(key)
        result.append(base + "/" + rel)
    return result
