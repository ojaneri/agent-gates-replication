import re

_IDENT = r"[0-9A-Za-z-]+"
_NUM = r"(?:0|[1-9][0-9]*)"
_VERSION_RE = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_IDENT}(?:\.{_IDENT})*))?"
    rf"(?:\+({_IDENT}(?:\.{_IDENT})*))?"
)


def _parse(version: str):
    """Return (core_tuple, prerelease_identifiers_or_None) or raise ValueError."""
    if not isinstance(version, str):
        raise ValueError(f"version must be a string, got {type(version).__name__}")
    m = _VERSION_RE.fullmatch(version)
    if m is None:
        raise ValueError(f"invalid version: {version!r}")
    major, minor, patch, pre, _build = m.groups()
    if pre is not None:
        for ident in pre.split("."):
            if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
                raise ValueError(f"numeric identifier with leading zero: {version!r}")
    core = (int(major), int(minor), int(patch))
    return core, (pre.split(".") if pre is not None else None)


def _identifier_key(ident: str):
    # Numeric identifiers sort below non-numeric ones; each group compares naturally.
    if ident.isdigit():
        return (0, int(ident), "")
    return (1, 0, ident)


def _prerelease_key(pre):
    if pre is None:
        # A release has higher precedence than any prerelease of the same core.
        return (1, ())
    return (0, tuple(_identifier_key(i) for i in pre))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    key_a = (core_a, _prerelease_key(pre_a))
    key_b = (core_b, _prerelease_key(pre_b))
    if key_a < key_b:
        return -1
    if key_a > key_b:
        return 1
    return 0
