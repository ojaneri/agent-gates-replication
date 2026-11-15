import re

_NUMERIC_RE = re.compile(r"0|[1-9][0-9]*")
_IDENT_RE = re.compile(r"[0-9A-Za-z-]+")
_CORE_PART_RE = re.compile(r"0|[1-9][0-9]*")


def _parse(version: str):
    """Parse a version string into (core_ints, prerelease_idents, valid).

    Raises ValueError for any invalid input.
    """
    if not isinstance(version, str):
        raise ValueError("version must be a string")

    # Build metadata: everything after the first '+'.
    build = None
    if "+" in version:
        version, build = version.split("+", 1)
        if build == "":
            raise ValueError("empty build metadata")
        for ident in build.split("."):
            if not _IDENT_RE.fullmatch(ident):
                raise ValueError("invalid build identifier")

    # Prerelease: everything after the first '-' (prerelease may contain '-').
    prerelease = None
    if "-" in version:
        version, prerelease = version.split("-", 1)
        if prerelease == "":
            raise ValueError("empty prerelease")
        pre_idents = prerelease.split(".")
        for ident in pre_idents:
            if not _IDENT_RE.fullmatch(ident):
                raise ValueError("invalid prerelease identifier")
            if ident.isascii() and ident.isdigit() and not _NUMERIC_RE.fullmatch(ident):
                raise ValueError("numeric prerelease identifier has leading zero")
    else:
        pre_idents = []

    # Core: exactly MAJOR.MINOR.PATCH.
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError("version core must have exactly three parts")
    core = []
    for part in parts:
        if not _CORE_PART_RE.fullmatch(part):
            raise ValueError("invalid numeric version part")
        core.append(int(part))

    return core, pre_idents


def _compare_pre_ident(x: str, y: str) -> int:
    x_num = x.isdigit()
    y_num = y.isdigit()
    if x_num and y_num:
        xi, yi = int(x), int(y)
        return (xi > yi) - (xi < yi)
    if x_num:
        return -1  # numeric has lower precedence than non-numeric
    if y_num:
        return 1
    return (x > y) - (x < y)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    if core_a != core_b:
        return -1 if core_a < core_b else 1

    # Same core: release (no prerelease) has higher precedence.
    if not pre_a and not pre_b:
        return 0
    if not pre_a:
        return 1
    if not pre_b:
        return -1

    for x, y in zip(pre_a, pre_b):
        c = _compare_pre_ident(x, y)
        if c != 0:
            return c

    if len(pre_a) == len(pre_b):
        return 0
    return -1 if len(pre_a) < len(pre_b) else 1
