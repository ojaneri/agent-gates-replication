import re
import string


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    base = dest.rstrip("/")

    planned: list[str] = []
    seen: set[str] = set()

    for member in members:
        if not isinstance(member, str):
            raise ValueError("archive member names must be strings")

        if "\x00" in member:
            raise UnsafePathError(f"NUL character in member name: {member!r}")

        if member[:1] in ("/", "\\"):
            raise UnsafePathError(f"absolute member name: {member!r}")

        if len(member) >= 2 and member[0] in string.ascii_letters and member[1] == ":":
            raise UnsafePathError(f"drive-prefixed member name: {member!r}")

        is_dir = member.endswith(("/", "\\"))

        stack: list[str] = []
        for segment in _SEPARATORS.split(member):
            if segment in ("", "."):
                continue
            if segment == "..":
                if not stack:
                    raise UnsafePathError(f"member escapes destination: {member!r}")
                stack.pop()
            else:
                stack.append(segment)

        if not stack:
            raise UnsafePathError(f"member is empty after normalisation: {member!r}")

        if is_dir:
            continue

        rel = "/".join(stack)
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate path (case-insensitive): {member!r}")
        seen.add(key)

        planned.append(f"{base}/{rel}")

    return planned
