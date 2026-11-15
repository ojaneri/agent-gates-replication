import re

_ID = r"[0-9A-Za-z-]+"
_NUM = r"(0|[1-9][0-9]*)"
_RE = re.compile(
    rf"\A{_NUM}\.{_NUM}\.{_NUM}(?:-({_ID}(?:\.{_ID})*))?(?:\+({_ID}(?:\.{_ID})*))?\Z",
    re.ASCII,
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.match(v)
    if not m:
        raise ValueError(f"invalid version: {v!r}")
    core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = None
    if m.group(4) is not None:
        pre = []
        for ident in m.group(4).split("."):
            if ident.isdigit():
                if len(ident) > 1 and ident[0] == "0":
                    raise ValueError(f"leading zero in {v!r}")
                pre.append((0, int(ident), ""))
            else:
                pre.append((1, 0, ident))
    return core, pre


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
    return _cmp(pa, pb)
