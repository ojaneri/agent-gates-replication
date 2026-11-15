class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _normalise(member: str) -> str:
    if "\x00" in member:
        raise UnsafePathError("NUL in member name")
    if member.startswith(("/", "\\")):
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
    return "/".join(out)


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    result = []
    seen = set()
    for member in members:
        norm = _normalise(member)
        if member.endswith(("/", "\\")):
            continue
        key = norm.lower()
        if key in seen:
            raise UnsafePathError("duplicate path: " + norm)
        seen.add(key)
        result.append(base + "/" + norm)
    return result
