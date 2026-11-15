import re

_NUM = r"(0|[1-9][0-9]*)"
_PRE_ID = r"(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(rf"^{_NUM}\.{_NUM}\.{_NUM}"
                 rf"(?:-(?P<pre>{_PRE_ID}(?:\.{_PRE_ID})*))?"
                 rf"(?:\+(?P<build>{_BUILD_ID}(?:\.{_BUILD_ID})*))?$")


def _parse(v: str):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _RE.fullmatch(v)
    if not m:
        raise ValueError(f"invalid version: {v!r}")
    core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = m.group("pre").split(".") if m.group("pre") is not None else None
    return core, pre


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def _cmp_pre(pa: list[str], pb: list[str]) -> int:
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


def compare_versions(a: str, b: str) -> int:
    ca, pa = _parse(a)
    cb, pb = _parse(b)
    c = _cmp(ca, cb)
    if c:
        return c
    if pa is None and pb is None:
        return 0
    if pa is None:
        return 1
    if pb is None:
        return -1
    return _cmp_pre(pa, pb)
