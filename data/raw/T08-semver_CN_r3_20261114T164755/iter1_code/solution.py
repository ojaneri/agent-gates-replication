import re

_NUM = r"(0|[1-9][0-9]*)"
_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(
    r"\A" + _NUM + r"\." + _NUM + r"\." + _NUM
    + r"(?:-(" + _ID + r"(?:\." + _ID + r")*))?"
    + r"(?:\+(" + _ID + r"(?:\." + _ID + r")*))?\Z"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.match(v)
    if not m:
        raise ValueError("invalid version: %r" % (v,))
    core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = m.group(4)
    ids = None
    if pre is not None:
        ids = pre.split(".")
        for i in ids:
            if i.isdigit() and len(i) > 1 and i[0] == "0":
                raise ValueError("leading zero in numeric identifier: %r" % (v,))
    return core, ids


def _cmp(x, y):
    return (x > y) - (x < y)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    ca, pa = _parse(a)
    cb, pb = _parse(b)
    if ca != cb:
        return _cmp(ca, cb)
    if pa is None and pb is None:
        return 0
    if pa is None:
        return 1
    if pb is None:
        return -1
    for x, y in zip(pa, pb):
        nx, ny = x.isdigit(), y.isdigit()
        if nx and ny:
            r = _cmp(int(x), int(y))
        elif nx:
            r = -1
        elif ny:
            r = 1
        else:
            r = _cmp(x, y)
        if r:
            return r
    return _cmp(len(pa), len(pb))
