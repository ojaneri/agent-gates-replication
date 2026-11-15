import re

_ID_CHARS = re.compile(r"^[0-9A-Za-z-]+$")
_NUMERIC = re.compile(r"^[0-9]+$")


def _parse_core(part: str, name: str) -> int:
    if not _NUMERIC.match(part):
        raise ValueError(f"invalid {name}: {part!r}")
    if len(part) > 1 and part[0] == "0":
        raise ValueError(f"leading zero in {name}: {part!r}")
    return int(part)


def _parse(version: str):
    if not isinstance(version, str):
        raise ValueError("version must be a string")

    # Build metadata: everything after the first '+'.
    build = None
    if "+" in version:
        version, build = version.split("+", 1)
        if build == "":
            raise ValueError("empty build metadata")
        for ident in build.split("."):
            if ident == "" or not _ID_CHARS.match(ident):
                raise ValueError(f"invalid build identifier: {ident!r}")

    # Prerelease: everything after the first '-' (core parts never contain '-').
    prerelease = None
    if "-" in version:
        version, prerelease = version.split("-", 1)
        if prerelease == "":
            raise ValueError("empty prerelease")
        pre_ids = prerelease.split(".")
        for ident in pre_ids:
            if ident == "" or not _ID_CHARS.match(ident):
                raise ValueError(f"invalid prerelease identifier: {ident!r}")
            if _NUMERIC.match(ident) and len(ident) > 1 and ident[0] == "0":
                raise ValueError(f"leading zero in numeric prerelease identifier: {ident!r}")
    else:
        pre_ids = None

    core = version.split(".")
    if len(core) != 3:
        raise ValueError(f"expected MAJOR.MINOR.PATCH, got {version!r}")
    major = _parse_core(core[0], "MAJOR")
    minor = _parse_core(core[1], "MINOR")
    patch = _parse_core(core[2], "PATCH")
    return (major, minor, patch), pre_ids


def _compare_pre_ident(x: str, y: str) -> int:
    x_num = _NUMERIC.match(x) is not None
    y_num = _NUMERIC.match(y) is not None
    if x_num and y_num:
        xi, yi = int(x), int(y)
        return (xi > yi) - (xi < yi)
    if x_num:
        return -1
    if y_num:
        return 1
    return (x > y) - (x < y)


def _compare_prerelease(xs, ys) -> int:
    for x, y in zip(xs, ys):
        c = _compare_pre_ident(x, y)
        if c != 0:
            return c
    return (len(xs) > len(ys)) - (len(xs) < len(ys))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    if core_a != core_b:
        return -1 if core_a < core_b else 1

    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1
    return _compare_prerelease(pre_a, pre_b)
