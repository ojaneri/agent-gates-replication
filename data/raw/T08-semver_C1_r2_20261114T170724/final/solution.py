"""Semantic version comparison following the rules in spec.md."""

import re

# ASCII-only identifier characters. Patterns use explicit classes rather than
# \d or \w so that Unicode digits/letters are rejected.
_CORE = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
_IDENT = r"[0-9A-Za-z-]+"
_IDENTS = rf"{_IDENT}(?:\.{_IDENT})*"
_VERSION_RE = re.compile(rf"{_CORE}(?:-({_IDENTS}))?(?:\+({_IDENTS}))?")


def _parse(version: str):
    """Parse and validate a version string.

    Returns ``((major, minor, patch), prerelease_key)`` where the prerelease key
    sorts so that a release without prerelease is greater than any prerelease.
    """
    match = _VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid version: {version!r}")

    core = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    prerelease = match.group(4)
    if prerelease is None:
        # No prerelease: higher than any version that has one.
        pre_key = (1,)
    else:
        identifiers = []
        for ident in prerelease.split("."):
            if ident.isdigit():
                if len(ident) > 1 and ident[0] == "0":
                    raise ValueError(f"numeric identifier has leading zero: {ident!r}")
                # Numeric identifiers sort before alphanumeric ones.
                identifiers.append((0, int(ident), ""))
            else:
                identifiers.append((1, 0, ident))
        pre_key = (0, tuple(identifiers))
    return core, pre_key


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    key_a = _parse(a)
    key_b = _parse(b)
    if key_a < key_b:
        return -1
    if key_a > key_b:
        return 1
    return 0
