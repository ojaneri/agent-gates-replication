class UnsafePathError(ValueError):
    """Raised when an archive member could escape the destination."""


def plan_extraction(dest: str, members: list[str]) -> list[str]:
    """Return target paths for the archive members. See spec.md."""
    raise NotImplementedError
