import re

_NUM = r"(0|[1-9][0-9]*)"
_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(
    rf"^{_NUM}\.{_NUM}\.{_NUM}(?:-({_ID}(?:\.{_ID})*))?(?:\+({_ID}(?:\.{_ID})*))?$"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.match(v)
    if not m or v.endswith("\n"):
        raise ValueError(f"invalid version: {v!r}")
    core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = m.group(4)
    ids = None
    if pre is not None:
        ids = pre.split(".")
        for i in ids:
            if i.isdigit() and len(i) > 1 and i[0] == "0":
                raise ValueError(f"leading zero in prerelease: {v!r}")
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
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            r = _cmp(int(x), int(y))
        elif xn:
            r = -1
        elif yn:
            r = 1
        else:
            r = _cmp(x, y)
        if r:
            return r
    return _cmp(len(pa), len(pb))
