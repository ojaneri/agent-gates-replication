import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def _is_drive_prefix(name: str) -> bool:
    return len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha()


def _normalise_member(member: str) -> tuple[list[str], bool]:
    """Return (segments, is_directory) for a member, or raise UnsafePathError."""
    if "\x00" in member:
        raise UnsafePathError(f"NUL character in member: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member: {member!r}")
    if _is_drive_prefix(member):
        raise UnsafePathError(f"drive-prefixed member: {member!r}")

    is_directory = member[-1:] in ("/", "\\")

    segments: list[str] = []
    for part in _SEPARATORS.split(member):
        if part == "" or part == ".":
            continue
        if part == "..":
            if not segments:
                raise UnsafePathError(f"member escapes destination: {member!r}")
            segments.pop()
        else:
            segments.append(part)

    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return segments, is_directory


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    base = dest.rstrip("/")  # "/" becomes "" (the root)

    targets: list[str] = []
    seen: set[str] = set()
    for member in members:
        segments, is_directory = _normalise_member(member)
        if is_directory:
            continue
        target = base + "/" + "/".join(segments)
        key = target.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate target (case-insensitive): {target!r}")
        seen.add(key)
        targets.append(target)
    return targets
