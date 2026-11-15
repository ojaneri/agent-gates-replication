import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


# A member name is split on both "/" and "\" (archives made on Windows use "\").
_SEPARATOR = re.compile(r"[\\/]")


def _is_drive_prefixed(name: str) -> bool:
    return len(name) >= 2 and name[0].isascii() and name[0].isalpha() and name[1] == ":"


def _normalise_member(member: str) -> tuple[list[str], bool]:
    """Validate one member and return (normalised segments, is_directory).

    Raises UnsafePathError if the member is unsafe.
    """
    if "\0" in member:
        raise UnsafePathError(f"NUL character in member: {member!r}")
    if member.startswith("/") or member.startswith("\\"):
        raise UnsafePathError(f"absolute member: {member!r}")
    if _is_drive_prefixed(member):
        raise UnsafePathError(f"drive-prefixed member: {member!r}")

    is_dir = member.endswith("/") or member.endswith("\\")

    segments: list[str] = []
    for part in _SEPARATOR.split(member):
        if part == "" or part == ".":
            continue
        if part == "..":
            if not segments:
                raise UnsafePathError(f"member climbs above destination: {member!r}")
            segments.pop()
        else:
            segments.append(part)

    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")

    return segments, is_dir


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    # Trailing "/" is ignored; "/" alone means the filesystem root.
    base = dest.rstrip("/")
    prefix = base + "/"

    targets: list[str] = []
    seen: set[str] = set()

    for member in members:
        if not isinstance(member, str):
            raise TypeError(f"member must be a string, not {type(member).__name__}")

        segments, is_dir = _normalise_member(member)
        if is_dir:
            # Directory entries are validated but not part of the plan.
            continue

        relative = "/".join(segments)
        key = relative.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate path (case-insensitive): {member!r}")
        seen.add(key)

        targets.append(prefix + relative)

    return targets
