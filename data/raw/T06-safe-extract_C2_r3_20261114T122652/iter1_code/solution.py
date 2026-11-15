class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def _destination_root(dest: str) -> str:
    """Return dest without trailing slashes; an empty result means the root."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")
    return dest.rstrip("/")


def _has_absolute_prefix(name: str) -> bool:
    """True for names that start with a separator or a Windows drive letter."""
    if name[:1] in ("/", "\\"):
        return True
    return len(name) >= 2 and name[1] == ":" and name[0].isascii() and name[0].isalpha()


def _split_segments(member: str) -> list[str]:
    """Normalise separators, '.' and '..' segments; raise if '..' climbs above the root."""
    segments: list[str] = []
    for part in member.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not segments:
                raise UnsafePathError(f"{member!r} climbs above the destination")
            segments.pop()
        else:
            segments.append(part)
    return segments


def _normalise_member(member: str) -> tuple[list[str], bool]:
    """Return (normalised segments, is_directory) or raise UnsafePathError."""
    if "\x00" in member:
        raise UnsafePathError(f"{member!r} contains a NUL character")
    if _has_absolute_prefix(member):
        raise UnsafePathError(f"{member!r} is absolute or has a drive prefix")
    is_dir = member.endswith(("/", "\\"))
    segments = _split_segments(member)
    if not segments:
        raise UnsafePathError(f"{member!r} is empty after normalisation")
    return segments, is_dir


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    root = _destination_root(dest)
    targets: list[str] = []
    seen: set[str] = set()
    for member in members:
        segments, is_dir = _normalise_member(member)
        if is_dir:
            continue
        rel = "/".join(segments)
        key = rel.lower()
        if key in seen:
            raise UnsafePathError(f"{member!r} duplicates an earlier member")
        seen.add(key)
        targets.append(f"{root}/{rel}")
    return targets
