import re

_NUM = r"(0|[1-9][0-9]*)"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(
    r"\A" + _NUM + r"\." + _NUM + r"\." + _NUM
    + r"(?:-(" + _PRE_ID + r"(?:\." + _PRE_ID + r")*))?"
    + r"(?:\+(" + _BUILD_ID + r"(?:\." + _BUILD_ID + r")*))?\Z"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.match(v)
    if not m:
        raise ValueError("invalid version: %r" % (v,))
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
        xn, yn = x.isdigit() and x.isascii(), y.isdigit() and y.isascii()
        if xn and yn:
            if int(x) != int(y):
                return _cmp(int(x), int(y))
        elif xn:
            return -1
        elif yn:
            return 1
        elif x != y:
            return _cmp(x, y)
    return _cmp(len(pa), len(pb))
