class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    base = dest.rstrip("/")  # "/" becomes "" so targets look like "/name"
    seen = set()
    targets = []

    for member in members:
        if "\0" in member:
            raise UnsafePathError(f"NUL character in member {member!r}")
        if member[:1] in ("/", "\\"):
            raise UnsafePathError(f"absolute member {member!r}")
        first = member[:1]
        if len(member) >= 2 and first.isascii() and first.isalpha() and member[1] == ":":
            raise UnsafePathError(f"drive-prefixed member {member!r}")

        is_dir = member.endswith(("/", "\\"))

        parts = []
        for seg in member.replace("\\", "/").split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                if not parts:
                    raise UnsafePathError(f"member {member!r} escapes destination")
                parts.pop()
            else:
                parts.append(seg)

        if not parts:
            raise UnsafePathError(f"member {member!r} is empty after normalisation")

        if is_dir:
            continue

        target = base + "/" + "/".join(parts)
        key = target.casefold()
        if key in seen:
            raise UnsafePathError(f"member {member!r} collides with an earlier member")
        seen.add(key)
        targets.append(target)

    return targets
