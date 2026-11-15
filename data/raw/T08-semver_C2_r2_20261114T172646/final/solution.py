import re

_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?"
)


def _valid_pre_ident(ident):
    if not ident:
        return False
    if ident.isdigit():
        return ident == "0" or ident[0] != "0"
    return True


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string")
    m = _VERSION.fullmatch(version)
    if m is None:
        raise ValueError("invalid version: %r" % (version,))
    major, minor, patch, pre, build = m.groups()
    pre_ids = None
    if pre is not None:
        pre_ids = pre.split(".")
        if not all(_valid_pre_ident(i) for i in pre_ids):
            raise ValueError("invalid prerelease: %r" % (version,))
    if build is not None and not all(build.split(".")):
        raise ValueError("invalid build: %r" % (version,))
    return (int(major), int(minor), int(patch)), pre_ids


def _cmp(x, y):
    return (x > y) - (x < y)


def _cmp_ident(x, y):
    x_num = x.isdigit()
    y_num = y.isdigit()
    if x_num and y_num:
        return _cmp(int(x), int(y))
    if x_num != y_num:
        return -1 if x_num else 1
    return _cmp(x, y)


def _cmp_pre(x, y):
    if x is None or y is None:
        return _cmp(x is None, y is None)
    for i, j in zip(x, y):
        c = _cmp_ident(i, j)
        if c:
            return c
    return _cmp(len(x), len(y))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    c = _cmp(core_a, core_b)
    if c:
        return c
    return _cmp_pre(pre_a, pre_b)
