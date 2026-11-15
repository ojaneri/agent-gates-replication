import re

# Character classes are spelled out explicitly so that only ASCII is accepted
# (\d and \w would also match non-ASCII Unicode characters).
_NUM = r"(?:0|[1-9][0-9]*)"
_IDENT = r"[0-9A-Za-z-]+"
_DOTTED = rf"{_IDENT}(?:\.{_IDENT})*"
_VERSION_RE = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_DOTTED}))?"
    rf"(?:\+({_DOTTED}))?"
)


def _parse(version: str):
    """Validate `version` and return (major, minor, patch, prerelease_or_None)."""
    if not isinstance(version, str):
        raise TypeError(f"version must be a str, not {type(version).__name__}")
    match = _VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid version: {version!r}")
    major, minor, patch, prerelease, _build = match.groups()
    if prerelease is not None:
        for ident in prerelease.split("."):
            # Numeric identifiers must not have leading zeros.
            if ident.isdigit() and ident.isascii() and len(ident) > 1 and ident[0] == "0":
                raise ValueError(f"numeric prerelease identifier has leading zero: {version!r}")
    return int(major), int(minor), int(patch), prerelease


def _identifier_key(ident: str):
    """Sort key for one prerelease identifier.

    Numeric identifiers sort before non-numeric ones; numeric ones compare
    by value, non-numeric ones compare as ASCII strings.
    """
    if ident.isdigit() and ident.isascii():
        return (0, int(ident), "")
    return (1, 0, ident)


def _precedence_key(version: str):
    major, minor, patch, prerelease = _parse(version)
    if prerelease is None:
        # A release (no prerelease) outranks any prerelease of the same core.
        return (major, minor, patch, 1, ())
    ids = tuple(_identifier_key(ident) for ident in prerelease.split("."))
    # Tuple comparison gives "fewer identifiers is lower" when one is a prefix.
    return (major, minor, patch, 0, ids)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    key_a = _precedence_key(a)
    key_b = _precedence_key(b)
    if key_a < key_b:
        return -1
    if key_a > key_b:
        return 1
    return 0
