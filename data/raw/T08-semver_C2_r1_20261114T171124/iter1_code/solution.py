import re

_NUM = r"(0|[1-9][0-9]*)"
_PRE_ID = r"(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"{_NUM}\.{_NUM}\.{_NUM}(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?(?:\+({_BUILD_ID}(?:\.{_BUILD_ID})*))?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string")
    m = _VERSION.fullmatch(version)
    if m is None:
        raise ValueError(f"invalid version: {version!r}")
    nums = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pre = m.group(4)
    return nums, (pre.split(".") if pre else [])


def _cmp(x, y):
    return (x > y) - (x < y)


def _cmp_identifier(x, y):
    xn, yn = x.isdigit(), y.isdigit()
    if xn and yn:
        return _cmp(int(x), int(y))
    if xn != yn:
        return -1 if xn else 1
    return _cmp(x, y)


def _cmp_prerelease(pa, pb):
    if not pa or not pb:
        return _cmp(len(pb), len(pa)) if not (pa and pb) else 0
    for x, y in zip(pa, pb):
        result = _cmp_identifier(x, y)
        if result:
            return result
    return _cmp(len(pa), len(pb))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    na, pa = _parse(a)
    nb, pb = _parse(b)
    if na != nb:
        return _cmp(na, nb)
    return _cmp_prerelease(pa, pb)
