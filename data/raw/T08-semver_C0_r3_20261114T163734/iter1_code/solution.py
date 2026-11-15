import re

_ID_CHARS = re.compile(r"^[0-9A-Za-z-]+$")
_NUMERIC = re.compile(r"^[0-9]+$")
_CORE_NUM = re.compile(r"^(0|[1-9][0-9]*)$")


def _parse_core(part: str, name: str, original: str) -> int:
    if not _CORE_NUM.fullmatch(part):
        raise ValueError(f"invalid {name} in version: {original!r}")
    return int(part)


def _parse(version: str):
    if not isinstance(version, str):
        raise ValueError(f"version must be a string: {version!r}")

    build = None
    rest = version
    if "+" in rest:
        rest, build = rest.split("+", 1)
        if build == "":
            raise ValueError(f"empty build metadata: {version!r}")
        build_ids = build.split(".")
        for ident in build_ids:
            if not ident or not _ID_CHARS.fullmatch(ident):
                raise ValueError(f"invalid build identifier in {version!r}")

    prerelease = None
    if "-" in rest:
        core, prerelease = rest.split("-", 1)
    else:
        core = rest
    # Note: a '-' inside the core would be caught by the core check below.

    parts = core.split(".")
    if len(parts) != 3:
        raise ValueError(f"version must be MAJOR.MINOR.PATCH: {version!r}")
    major = _parse_core(parts[0], "MAJOR", version)
    minor = _parse_core(parts[1], "MINOR", version)
    patch = _parse_core(parts[2], "PATCH", version)

    pre_ids = None
    if prerelease is not None:
        pre_ids = prerelease.split(".")
        for ident in pre_ids:
            if not ident or not _ID_CHARS.fullmatch(ident):
                raise ValueError(f"invalid prerelease identifier in {version!r}")
            if _NUMERIC.fullmatch(ident) and len(ident) > 1 and ident[0] == "0":
                raise ValueError(f"numeric prerelease identifier has leading zero: {version!r}")

    return (major, minor, patch), pre_ids


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def _compare_prerelease(a_ids, b_ids) -> int:
    for x, y in zip(a_ids, b_ids):
        x_num = bool(_NUMERIC.fullmatch(x))
        y_num = bool(_NUMERIC.fullmatch(y))
        if x_num and y_num:
            c = _cmp(int(x), int(y))
        elif x_num:
            c = -1
        elif y_num:
            c = 1
        else:
            c = _cmp(x, y)
        if c != 0:
            return c
    return _cmp(len(a_ids), len(b_ids))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    a_core, a_pre = _parse(a)
    b_core, b_pre = _parse(b)

    c = _cmp(a_core, b_core)
    if c != 0:
        return c

    if a_pre is None and b_pre is None:
        return 0
    if a_pre is None:
        return 1
    if b_pre is None:
        return -1
    return _compare_prerelease(a_pre, b_pre)
