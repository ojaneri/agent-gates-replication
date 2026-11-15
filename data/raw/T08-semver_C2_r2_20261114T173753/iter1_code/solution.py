import re

_IDENT = re.compile(r"[0-9A-Za-z-]+")
_DIGITS = re.compile(r"[0-9]+")
_NUMBER = re.compile(r"0|[1-9][0-9]*")


def _check_build(build):
    for ident in build.split("."):
        if not _IDENT.fullmatch(ident):
            raise ValueError(f"invalid build identifier: {ident!r}")


def _check_prerelease(prerelease):
    for ident in prerelease.split("."):
        if not _IDENT.fullmatch(ident):
            raise ValueError(f"invalid prerelease identifier: {ident!r}")
        if _DIGITS.fullmatch(ident) and not _NUMBER.fullmatch(ident):
            raise ValueError(f"numeric identifier has leading zero: {ident!r}")
    return prerelease.split(".")


def _parse_core(core):
    parts = core.split(".")
    if len(parts) != 3 or not all(_NUMBER.fullmatch(p) for p in parts):
        raise ValueError(f"invalid core version: {core!r}")
    return tuple(int(p) for p in parts)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string")
    main, plus, build = version.partition("+")
    if plus:
        _check_build(build)
    core, dash, prerelease = main.partition("-")
    numbers = _parse_core(core)
    if dash:
        return numbers, _check_prerelease(prerelease)
    return numbers, None


def _identifier_key(ident):
    if _DIGITS.fullmatch(ident):
        return (0, int(ident), "")
    return (1, 0, ident)


def _precedence_key(version):
    numbers, identifiers = _parse(version)
    if identifiers is None:
        return numbers, 1, ()
    return numbers, 0, tuple(_identifier_key(i) for i in identifiers)


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    key_a = _precedence_key(a)
    key_b = _precedence_key(b)
    return (key_a > key_b) - (key_a < key_b)
