class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _reject_absolute_or_nul(member):
    """Refuse NUL characters, POSIX/Windows absolute paths and drive prefixes."""
    if "\x00" in member:
        raise UnsafePathError(f"NUL character in member: {member!r}")
    if member[:1] in ("/", "\\"):
        raise UnsafePathError(f"absolute member: {member!r}")
    if len(member) >= 2 and member[1] == ":" and member[0].isascii() and member[0].isalpha():
        raise UnsafePathError(f"drive-prefixed member: {member!r}")


def _normalise(member):
    """Return (normalised_path, is_directory) or raise UnsafePathError."""
    _reject_absolute_or_nul(member)
    is_directory = member.endswith(("/", "\\"))
    segments = []
    for segment in member.replace("\\", "/").split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not segments:
                raise UnsafePathError(f"member escapes destination: {member!r}")
            segments.pop()
        else:
            segments.append(segment)
    if not segments:
        raise UnsafePathError(f"member is empty after normalisation: {member!r}")
    return "/".join(segments), is_directory


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")
    prefix = dest.rstrip("/")
    targets = []
    seen = set()
    for member in members:
        normalised, is_directory = _normalise(member)
        if is_directory:
            continue
        key = normalised.casefold()
        if key in seen:
            raise UnsafePathError(f"duplicate target: {member!r}")
        seen.add(key)
        targets.append(prefix + "/" + normalised)
    return targets
