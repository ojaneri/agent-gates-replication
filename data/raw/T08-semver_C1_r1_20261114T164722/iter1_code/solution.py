import re

_ID = r"[0-9A-Za-z-]+"
_NUM = r"(?:0|[1-9][0-9]*)"
_PRE_ID = rf"(?:{_NUM}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_RE = re.compile(
    rf"\A({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?"
    rf"(?:\+({_ID}(?:\.{_ID})*))?\Z"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.match(v)
    if not m:
        raise ValueError(f"invalid version: {v!r}")
    pre = m.group(4).split(".") if m.group(4) is not None else None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))), pre


def _cmp(x, y):
    return (x > y) - (x < y)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    na, pa = _parse(a)
    nb, pb = _parse(b)
    if na != nb:
        return _cmp(na, nb)
    if pa is None or pb is None:
        if pa is None and pb is None:
            return 0
        return 1 if pa is None else -1
    for x, y in zip(pa, pb):
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd:
            r = _cmp(int(x), int(y))
        elif xd:
            r = -1
        elif yd:
            r = 1
        else:
            r = _cmp(x, y)
        if r:
            return r
    return _cmp(len(pa), len(pb))
