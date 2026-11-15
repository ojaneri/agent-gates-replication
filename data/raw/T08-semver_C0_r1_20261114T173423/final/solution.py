import re

# Non-capturing sub-patterns so that group(1) = core, group(2) = prerelease,
# group(3) = build.
_NUM = r"(?:0|[1-9][0-9]*)"
_IDENT = r"[0-9A-Za-z-]+"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
_FULL_RE = re.compile(
    rf"({_NUM}\.{_NUM}\.{_NUM})"
    rf"(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?"
    rf"(?:\+({_IDENT}(?:\.{_IDENT})*))?"
)


def _parse(version: str):
    """Return ((major, minor, patch), prerelease_identifiers_or_None).

    Raises ValueError for anything that is not a valid version string.
    """
    if not isinstance(version, str):
        raise ValueError(f"version must be a str, got {type(version).__name__}")
    m = _FULL_RE.fullmatch(version)
    if m is None:
        raise ValueError(f"invalid version: {version!r}")
    core = tuple(int(x) for x in m.group(1).split("."))
    pre = m.group(2)
    prerelease = pre.split(".") if pre is not None else None
    return core, prerelease


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def _compare_identifier(x: str, y: str) -> int:
    x_num = x.isdigit()
    y_num = y.isdigit()
    if x_num and y_num:
        return _cmp(int(x), int(y))
    if x_num:
        return -1  # numeric < non-numeric
    if y_num:
        return 1
    return _cmp(x, y)  # ASCII string comparison


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    result = _cmp(core_a, core_b)
    if result != 0:
        return result

    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1  # release > prerelease
    if pre_b is None:
        return -1

    for x, y in zip(pre_a, pre_b):
        result = _compare_identifier(x, y)
        if result != 0:
            return result
    return _cmp(len(pre_a), len(pre_b))
