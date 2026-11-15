from itertools import groupby


def _encode_run(c: str, n: int) -> str:
    if n >= 4:
        return "~" + str(n) + "~" + c
    return c * n if c != "~" else "~~" * n


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    return "".join(_encode_run(c, len(list(g))) for c, g in groupby(s))


def _read_count(t: str, i: int):
    """Parse a count starting at i; return (count, index after it)."""
    j = i
    while j < len(t) and t[j] in "0123456789":
        j += 1
    digits = t[i:j]
    if not digits or digits[0] == "0":
        raise ValueError("bad count")
    n = int(digits)
    if n < 4:
        raise ValueError("count below 4")
    return n, j


def _read_escape(t: str, i: int):
    """Handle an escape at t[i] == '~'; return (text, next index)."""
    if i + 1 >= len(t):
        raise ValueError("dangling ~")
    if t[i + 1] == "~":
        return "~", i + 2
    n, j = _read_count(t, i + 1)
    if j >= len(t) or t[j] != "~":
        raise ValueError("count not followed by ~")
    if j + 1 >= len(t):
        raise ValueError("missing character")
    return t[j + 1] * n, j + 2


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    while i < len(t):
        if t[i] == "~":
            text, i = _read_escape(t, i)
        else:
            text, i = t[i], i + 1
        out.append(text)
    return "".join(out)
