import re
import string


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def _normalise(member):
    """Return (segments, is_directory) for one member, or raise UnsafePathError."""
    if not isinstance(member, str):
        raise TypeError("archive member names must be strings")
    if "\x00" in member:
        raise UnsafePathError(f"member contains NUL: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"member is absolute: {member!r}")
    if len(member) >= 2 and member[0] in string.ascii_letters and member[1] == ":":
        raise UnsafePathError(f"member has a drive prefix: {member!r}")

    is_directory = member.endswith(("/", "\\"))
    segments = []
    for segment in _SEPARATORS.split(member):
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
    return segments, is_directory


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    # "/" (or "//") becomes "", so targets are "/name" for the root.
    prefix = dest.rstrip("/")

    # Validate every member before returning anything: never a partial plan.
    targets = []
    seen = set()
    for member in members:
        segments, is_directory = _normalise(member)
        if is_directory:
            continue
        relative = "/".join(segments)
        key = relative.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate target (case-insensitive): {member!r}")
        seen.add(key)
        targets.append(f"{prefix}/{relative}")
    return targets
