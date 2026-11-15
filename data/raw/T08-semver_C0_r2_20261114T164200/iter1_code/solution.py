import re

_NUMERIC_RE = re.compile(r"0|[1-9][0-9]*")
_IDENT_RE = re.compile(r"[A-Za-z0-9-]+")
_CORE_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def _parse(version: str):
    if not isinstance(version, str):
        raise ValueError("version must be a string")
    rest = version
    build = None
    if "+" in rest:
        rest, build = rest.split("+", 1)
        parts = build.split(".")
        if not all(p and _IDENT_RE.fullmatch(p) for p in parts):
            raise ValueError(f"invalid build metadata: {version!r}")
    pre = None
    if "-" in rest:
        # The core never contains '-', so the first '-' starts the prerelease.
        rest, pre = rest.split("-", 1)
    m = _CORE_RE.fullmatch(rest)
    if m is None:
        raise ValueError(f"invalid version: {version!r}")
    core = tuple(int(x) for x in m.groups())
    pre_ids = None
    if pre is not None:
        ids = pre.split(".")
        pre_ids = []
        for ident in ids:
            if not ident or not _IDENT_RE.fullmatch(ident):
                raise ValueError(f"invalid prerelease: {version!r}")
            if ident.isdigit():
                if not _NUMERIC_RE.fullmatch(ident):
                    raise ValueError(f"numeric identifier with leading zero: {version!r}")
                pre_ids.append((0, int(ident), ""))
            else:
                pre_ids.append((1, 0, ident))
    return core, pre_ids


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    c = _cmp(core_a, core_b)
    if c != 0:
        return c

    # No prerelease > has prerelease.
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1

    for ia, ib in zip(pre_a, pre_b):
        c = _cmp(ia, ib)
        if c != 0:
            return c
    return _cmp(len(pre_a), len(pre_b))
