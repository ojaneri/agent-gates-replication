import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def _normalise(member: str) -> str:
    """Return the normalised relative path of an archive member.

    Raises UnsafePathError if the member is unsafe or empty after normalisation.
    """
    if "\x00" in member:
        raise UnsafePathError(f"NUL character in member: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member: {member!r}")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError(f"drive-prefixed member: {member!r}")

    parts: list[str] = []
    for segment in _SEPARATORS.split(member):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not parts:
                raise UnsafePathError(f"member escapes destination: {member!r}")
            parts.pop()
        else:
            parts.append(segment)

    if not parts:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return "/".join(parts)


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    prefix = dest.rstrip("/")
    plan: list[str] = []
    seen: set[str] = set()

    for member in members:
        relative = _normalise(member)
        if member.endswith(("/", "\\")):
            # Directory entry: validated above, but not extracted as a file.
            continue
        key = relative.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate target path: {member!r}")
        seen.add(key)
        plan.append(f"{prefix}/{relative}")

    return plan
