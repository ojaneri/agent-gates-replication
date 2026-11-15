import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def _normalise_member(member: str) -> tuple[str, bool]:
    """Return (normalised relative path, is_directory_entry) or raise UnsafePathError."""
    if "\0" in member:
        raise UnsafePathError(f"member contains a NUL character: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"member is absolute: {member!r}")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError(f"member has a drive prefix: {member!r}")

    is_dir = member.endswith(("/", "\\"))

    stack: list[str] = []
    for segment in _SEPARATORS.split(member):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not stack:
                raise UnsafePathError(f"member escapes the destination: {member!r}")
            stack.pop()
        else:
            stack.append(segment)

    if not stack:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return "/".join(stack), is_dir


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")
    base = dest.rstrip("/")

    planned: list[str] = []
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, str):
            raise ValueError(f"member must be a string, not {type(member).__name__}")
        rel, is_dir = _normalise_member(member)
        if is_dir:
            continue
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError(f"two members map to the same path: {member!r}")
        seen.add(key)
        planned.append(f"{base}/{rel}")
    return planned
