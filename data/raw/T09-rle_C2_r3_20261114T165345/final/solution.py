from itertools import groupby


def _encode_run(ch: str, n: int) -> str:
    if n >= 4:
        return "~" + str(n) + "~" + ch
    if ch == "~":
        return "~~" * n
    return ch * n


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    return "".join(_encode_run(ch, len(list(g))) for ch, g in groupby(s))


def _parse_run(t: str, i: int):
    """Parse a run starting at the '~' at index i. Returns (text, next_index)."""
    j = i + 1
    while j < len(t) and t[j] in "0123456789":
        j += 1
    digits = t[i + 1:j]
    if not digits or digits[0] == "0" or int(digits) < 4:
        raise ValueError("invalid run count")
    if j >= len(t) or t[j] != "~":
        raise ValueError("count not followed by '~'")
    if j + 1 >= len(t):
        raise ValueError("missing run character")
    return t[j + 1] * int(digits), j + 2


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    while i < len(t):
        if t[i] != "~":
            out.append(t[i])
            i += 1
        elif t[i + 1:i + 2] == "~":
            out.append("~")
            i += 2
        else:
            text, i = _parse_run(t, i)
            out.append(text)
    return "".join(out)
