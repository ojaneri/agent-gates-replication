import re

_CORE_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_IDENT_RE = re.compile(r"[0-9A-Za-z-]+")


def _check_identifiers(idents, no_leading_zeros):
    """Raise ValueError if any identifier is malformed."""
    for ident in idents:
        if _IDENT_RE.fullmatch(ident) is None:
            raise ValueError(f"invalid identifier: {ident!r}")
        if no_leading_zeros and ident.isdigit() and len(ident) > 1 and ident[0] == "0":
            raise ValueError(f"numeric identifier has leading zero: {ident!r}")


def _parse(version):
    """Split a version string into ((major, minor, patch), prerelease_identifiers)."""
    if not isinstance(version, str):
        raise ValueError("version must be a string")
    main, plus, build = version.partition("+")
    if plus:
        _check_identifiers(build.split("."), no_leading_zeros=False)
    core, dash, pre = main.partition("-")
    match = _CORE_RE.fullmatch(core)
    if match is None:
        raise ValueError(f"invalid version: {version!r}")
    pre_ids = []
    if dash:
        pre_ids = pre.split(".")
        _check_identifiers(pre_ids, no_leading_zeros=True)
    return tuple(int(group) for group in match.groups()), pre_ids


def _identifier_key(ident):
    """Numeric identifiers sort before alphanumeric ones; each kind sorts naturally."""
    if ident.isdigit():
        return (0, int(ident), "")
    return (1, 0, ident)


def _precedence_key(version):
    """Build a tuple that orders versions according to the spec."""
    core, pre_ids = _parse(version)
    if not pre_ids:
        # A release outranks any prerelease with the same core.
        return core + (1, ())
    return core + (0, tuple(_identifier_key(ident) for ident in pre_ids))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    key_a = _precedence_key(a)
    key_b = _precedence_key(b)
    return (key_a > key_b) - (key_a < key_b)
