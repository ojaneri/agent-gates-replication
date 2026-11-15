import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


# Both "/" and "\" separate segments, since archives made on Windows use "\".
_SEPARATOR = re.compile(r"[/\\]")
# A Windows drive prefix: an ASCII letter followed by ":".
_DRIVE_PREFIX = re.compile(r"[A-Za-z]:")


def _is_directory_entry(member: str) -> bool:
    return member.endswith(("/", "\\"))


def _normalise(member: str) -> list[str]:
    """Validate one member and return its normalised segments.

    Raises UnsafePathError if the member could write outside the destination
    or normalises to nothing.
    """
    if "\x00" in member:
        raise UnsafePathError(f"NUL character in member: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member: {member!r}")
    if _DRIVE_PREFIX.match(member):
        raise UnsafePathError(f"drive-prefixed member: {member!r}")

    segments: list[str] = []
    for segment in _SEPARATOR.split(member):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not segments:
                raise UnsafePathError(f"member climbs above destination: {member!r}")
            segments.pop()
        else:
            segments.append(segment)

    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return segments


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    prefix = dest.rstrip("/")
    targets: list[str] = []
    seen: set[str] = set()

    for member in members:
        segments = _normalise(member)  # validates directory entries too
        if _is_directory_entry(member):
            continue

        relative = "/".join(segments)
        key = relative.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate target path: {member!r}")
        seen.add(key)
        targets.append(prefix + "/" + relative)

    return targets
