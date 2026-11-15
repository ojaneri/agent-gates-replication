class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    result = []
    seen = set()
    for name in members:
        if "\x00" in name:
            raise UnsafePathError(name)
        if name.startswith("/") or name.startswith("\\"):
            raise UnsafePathError(name)
        if len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha():
            raise UnsafePathError(name)
        is_dir = name.endswith("/") or name.endswith("\\")
        parts = []
        for seg in name.replace("\\", "/").split("/"):
            if seg == "" or seg == ".":
                continue
            if seg == "..":
                if not parts:
                    raise UnsafePathError(name)
                parts.pop()
            else:
                parts.append(seg)
        if not parts:
            raise UnsafePathError(name)
        if is_dir:
            continue
        norm = "/".join(parts)
        key = norm.lower()
        if key in seen:
            raise UnsafePathError(name)
        seen.add(key)
        result.append(base + "/" + norm)
    return result
