import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


# Both "/" and "\" separate path segments (archives made on Windows use "\").
_SEPARATOR = re.compile(r"[/\\]")


def _has_drive_prefix(name: str) -> bool:
    """True for names starting with an ASCII letter followed by ':' (e.g. C:/x, c:x)."""
    return len(name) >= 2 and name[0].isascii() and name[0].isalpha() and name[1] == ":"


def _normalise(member: str) -> tuple[list[str], bool]:
    """Return (segments, is_directory) for a member, or raise UnsafePathError."""
    if "\x00" in member:
        raise UnsafePathError(f"member contains a NUL character: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"member is absolute: {member!r}")
    if _has_drive_prefix(member):
        raise UnsafePathError(f"member starts with a drive prefix: {member!r}")

    is_directory = member.endswith(("/", "\\"))

    segments: list[str] = []
    for segment in _SEPARATOR.split(member):
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if not segments:
                raise UnsafePathError(f"member climbs above the destination: {member!r}")
            segments.pop()
        else:
            segments.append(segment)

    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return segments, is_directory


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    # Trailing "/" characters are ignored; "/" alone means the root, so base becomes "".
    base = dest.rstrip("/")

    plan: list[str] = []
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, str):
            raise TypeError(f"archive member names must be strings, got {type(member).__name__}")

        segments, is_directory = _normalise(member)
        if is_directory:
            # Directory entries are validated but not extracted as files.
            continue

        relative = "/".join(segments)
        folded = relative.casefold()
        if folded in seen:
            raise UnsafePathError(f"two members map to the same path: {relative!r}")
        seen.add(folded)

        plan.append(f"{base}/{relative}")

    return plan
