import re

_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(" + _ID + r"(?:\." + _ID + r")*))?"
    r"(?:\+(" + _ID + r"(?:\." + _ID + r")*))?"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.fullmatch(v)
    if not m:
        raise ValueError("invalid version: %r" % (v,))
    nums = tuple(int(m.group(i)) for i in (1, 2, 3))
    pre = None
    if m.group(4) is not None:
        pre = m.group(4).split(".")
        for p in pre:
            if p.isdigit() and len(p) > 1 and p[0] == "0":
                raise ValueError("leading zero in prerelease: %r" % (v,))
    return nums, pre


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
