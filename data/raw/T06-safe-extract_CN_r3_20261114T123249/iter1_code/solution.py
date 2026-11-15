class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    result = []
    seen = set()
    for m in members:
        if "\x00" in m:
            raise UnsafePathError("NUL in member name")
        if m.startswith("/") or m.startswith("\\"):
            raise UnsafePathError("absolute path")
        if len(m) >= 2 and m[1] == ":" and m[0].isascii() and m[0].isalpha():
            raise UnsafePathError("drive prefix")
        is_dir = m.endswith("/") or m.endswith("\\")
        parts = []
        for seg in m.replace("\\", "/").split("/"):
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
        if is_dir:
            continue
        norm = "/".join(parts)
        key = norm.lower()
        if key in seen:
            raise UnsafePathError("duplicate target: " + norm)
        seen.add(key)
        result.append(base + "/" + norm)
    return result
