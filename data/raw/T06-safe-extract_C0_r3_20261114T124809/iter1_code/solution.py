import re
import string


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[\\/]")
_ASCII_LETTERS = frozenset(string.ascii_letters)


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    base = dest.rstrip("/")
    seen: set[str] = set()
    targets: list[str] = []

    for member in members:
        if "\x00" in member:
            raise UnsafePathError(f"NUL character in member {member!r}")
        if member[:1] in ("/", "\\"):
            raise UnsafePathError(f"absolute member {member!r}")
        if len(member) >= 2 and member[1] == ":" and member[0] in _ASCII_LETTERS:
            raise UnsafePathError(f"drive-prefixed member {member!r}")

        is_dir = member.endswith(("/", "\\"))

        parts: list[str] = []
        for segment in _SEPARATORS.split(member):
            if segment in ("", "."):
                continue
            if segment == "..":
                if not parts:
                    raise UnsafePathError(f"member {member!r} climbs above destination")
                parts.pop()
            else:
                parts.append(segment)

        if not parts:
            raise UnsafePathError(f"member {member!r} is empty after normalisation")

        if is_dir:
            continue

        rel = "/".join(parts)
        key = rel.casefold()
        if key in seen:
            raise UnsafePathError(f"member {member!r} collides with an earlier member")
        seen.add(key)

        targets.append(f"{base}/{rel}" if base else f"/{rel}")

    return targets
