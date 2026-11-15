import re

_DRIVE = re.compile(r"^[A-Za-z]:")


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _normalize(member: str) -> str:
    if "\x00" in member:
        raise UnsafePathError("NUL character")
    name = member.replace("\\", "/")
    if name.startswith("/") or _DRIVE.match(name):
        raise UnsafePathError("absolute path")
    parts: list[str] = []
    for seg in name.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise UnsafePathError("escapes destination")
            parts.pop()
        else:
            parts.append(seg)
    if not parts:
        raise UnsafePathError("empty path")
    return "/".join(parts)


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    if not isinstance(dest, str) or not dest:
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")
    seen: set[str] = set()
    out: list[str] = []
    for member in members:
        norm = _normalize(member)
        if member.replace("\\", "/").endswith("/"):
            continue
        key = norm.lower()
        if key in seen:
            raise UnsafePathError("duplicate target")
        seen.add(key)
        out.append(f"{base}/{norm}")
    return out
