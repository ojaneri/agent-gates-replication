import re

_NUM = r"(?:0|[1-9][0-9]*)"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?"
    rf"(?:\+{_BUILD_ID}(?:\.{_BUILD_ID})*)?"
)


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _VERSION.fullmatch(v)
    if m is None:
        raise ValueError("invalid version: %r" % (v,))
    core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = m.group(4)
    return core, (pre.split(".") if pre is not None else None)


def _cmp(x, y):
    return (x > y) - (x < y)


def _cmp_ident(x, y):
    xn, yn = x.isdigit(), y.isdigit()
    if xn and yn:
        return _cmp(int(x), int(y))
    if xn != yn:
        return -1 if xn else 1
    return _cmp(x, y)


def _cmp_pre(p, q):
    if p is None or q is None:
        return _cmp(p is None, q is None)
    for x, y in zip(p, q):
        c = _cmp_ident(x, y)
        if c:
            return c
    return _cmp(len(p), len(q))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    c = _cmp(core_a, core_b)
    if c:
        return c
    return _cmp_pre(pre_a, pre_b)
