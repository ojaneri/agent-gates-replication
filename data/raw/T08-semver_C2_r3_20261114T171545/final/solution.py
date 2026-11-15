"""Semantic version comparison. See spec.md."""

import re

_CORE_NUMBER = re.compile(r"0|[1-9][0-9]*")
_IDENTIFIER = re.compile(r"[0-9A-Za-z-]+")


def _cmp(x, y):
    return (x > y) - (x < y)


def _identifiers(text, allow_leading_zeros):
    """Validate a dot-separated identifier list and return it as a list."""
    parts = text.split(".")
    for part in parts:
        if not _IDENTIFIER.fullmatch(part):
            raise ValueError(f"invalid identifier: {part!r}")
        if not allow_leading_zeros and part.isdigit() and part[0] == "0" and len(part) > 1:
            raise ValueError(f"numeric identifier has leading zero: {part!r}")
    return parts


def _parse(version):
    """Return ((major, minor, patch), prerelease_identifiers_or_None)."""
    core_and_pre, plus, build = version.partition("+")
    if plus:
        _identifiers(build, allow_leading_zeros=True)
    core, dash, pre = core_and_pre.partition("-")
    parts = core.split(".")
    if len(parts) != 3 or not all(_CORE_NUMBER.fullmatch(p) for p in parts):
        raise ValueError(f"invalid version: {version!r}")
    numbers = tuple(int(p) for p in parts)
    prerelease = _identifiers(pre, allow_leading_zeros=False) if dash else None
    return numbers, prerelease


def _compare_identifier(x, y):
    x_num, y_num = x.isdigit(), y.isdigit()
    if x_num and y_num:
        return _cmp(int(x), int(y))
    if x_num:
        return -1
    if y_num:
        return 1
    return _cmp(x, y)


def _compare_prerelease(pa, pb):
    for x, y in zip(pa, pb):
        result = _compare_identifier(x, y)
        if result:
            return result
    return _cmp(len(pa), len(pb))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    if core_a != core_b:
        return _cmp(core_a, core_b)
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1
    return _compare_prerelease(pre_a, pre_b)
