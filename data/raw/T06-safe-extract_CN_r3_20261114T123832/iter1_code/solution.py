import re


class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


_SEPARATORS = re.compile(r"[/\\]")


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    if not isinstance(dest, str) or dest == "":
        raise ValueError("dest must be a non-empty string")

    # Trailing slashes are ignored; "/" becomes "" so targets look like "/name".
    prefix = dest.rstrip("/")

    plans: list[str] = []
    seen: set[str] = set()

    for member in members:
        if not isinstance(member, str):
            raise ValueError("archive member names must be strings")

        if "\0" in member:
            raise UnsafePathError(f"NUL character in member: {member!r}")

        # Absolute paths (POSIX or Windows style).
        if member.startswith(("/", "\\")):
            raise UnsafePathError(f"absolute member path: {member!r}")

        # Windows drive prefix such as "C:/x", "c:x" or "C:\\x".
        if len(member) >= 2 and member[0].isascii() and member[0].isalpha() and member[1] == ":":
            raise UnsafePathError(f"drive-prefixed member path: {member!r}")

        # A trailing separator marks a directory entry.
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
            raise UnsafePathError(f"duplicate target path: {member!r}")
        seen.add(key)

        plans.append(f"{prefix}/{rel}")

    return plans
