import re

_ID = r"[0-9A-Za-z-]+"
_NUM = r"(?:0|[1-9][0-9]*)"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_RE = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?"
    rf"(?:\+({_ID}(?:\.{_ID})*))?"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.fullmatch(v)
    if not m:
        raise ValueError(f"invalid version: {v!r}")
    major, minor, patch, pre, _ = m.groups()
    return (int(major), int(minor), int(patch)), (pre.split(".") if pre else None)


def _cmp(x, y):
    return (x > y) - (x < y)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    na, pa = _parse(a)
    nb, pb = _parse(b)
    if na != nb:
        return _cmp(na, nb)
    if pa is None and pb is None:
        return 0
    if pa is None:
        return 1
    if pb is None:
        return -1
    for x, y in zip(pa, pb):
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            c = _cmp(int(x), int(y))
        elif xn:
            c = -1
        elif yn:
            c = 1
        else:
            c = _cmp(x, y)
        if c:
            return c
    return _cmp(len(pa), len(pb))
