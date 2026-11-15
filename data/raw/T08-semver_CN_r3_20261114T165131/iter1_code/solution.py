import re

# ASCII-only patterns (avoid \d, which matches non-ASCII digits in Python 3).
_NUMERIC_CORE = re.compile(r"0|[1-9][0-9]*")
_IDENT = re.compile(r"[0-9A-Za-z-]+")
_DIGITS = re.compile(r"[0-9]+")


def _parse(v):
    """Parse a version string into (core_tuple, prerelease_identifiers).

    prerelease_identifiers is a list of (is_numeric, value) pairs; it is
    empty when the version has no prerelease. Raises ValueError if invalid.
    """
    if not isinstance(v, str):
        raise ValueError("version must be a string")

    # BUILD is everything after the first '+'; it is validated but ignored.
    main, plus, build = v.partition("+")
    if plus:
        for ident in build.split("."):
            if not _IDENT.fullmatch(ident):
                raise ValueError(f"invalid build identifier in {v!r}")

    # PRERELEASE is everything after the first '-' (core never contains '-').
    core_str, dash, pre_str = main.partition("-")

    core_parts = core_str.split(".")
    if len(core_parts) != 3:
        raise ValueError(f"invalid version core in {v!r}")
    core = []
    for part in core_parts:
        if not _NUMERIC_CORE.fullmatch(part):
            raise ValueError(f"invalid numeric component in {v!r}")
        core.append(int(part))

    pre = []
    if dash:
        for ident in pre_str.split("."):
            if not _IDENT.fullmatch(ident):
                raise ValueError(f"invalid prerelease identifier in {v!r}")
            if _DIGITS.fullmatch(ident):
                if len(ident) > 1 and ident[0] == "0":
                    raise ValueError(f"leading zero in numeric identifier in {v!r}")
                pre.append((0, int(ident)))
            else:
                pre.append((1, ident))

    return tuple(core), pre


def _key(parsed):
    core, pre = parsed
    if not pre:
        # A release outranks any prerelease with the same core.
        return (core, 1, ())
    return (core, 0, tuple(pre))


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. See spec.md."""
    ka = _key(_parse(a))
    kb = _key(_parse(b))
    if ka < kb:
        return -1
    if ka > kb:
        return 1
    return 0
