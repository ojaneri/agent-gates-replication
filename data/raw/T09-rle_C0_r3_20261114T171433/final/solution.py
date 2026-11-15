from itertools import groupby

_DIGITS = "0123456789"


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    parts = []
    for c, group in groupby(s):
        n = sum(1 for _ in group)
        if n >= 4:
            parts.append(f"~{n}~{c}")
        elif c == "~":
            parts.append("~~" * n)
        else:
            parts.append(c * n)
    return "".join(parts)


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    n = len(t)
    while i < n:
        ch = t[i]
        if ch != "~":
            out.append(ch)
            i += 1
            continue

        # ch is '~': it must start "~~" or "~<count>~<c>".
        if i + 1 >= n:
            raise ValueError("'~' at end of input")
        nxt = t[i + 1]
        if nxt == "~":
            out.append("~")
            i += 2
            continue
        if nxt not in _DIGITS:
            raise ValueError(f"invalid character {nxt!r} after '~' at index {i}")

        j = i + 1
        while j < n and t[j] in _DIGITS:
            j += 1
        digits = t[i + 1:j]
        if digits[0] == "0":
            raise ValueError(f"count with leading zero at index {i}")
        count = int(digits)
        if count < 4:
            raise ValueError(f"count {count} below 4 at index {i}")
        if j >= n or t[j] != "~":
            raise ValueError(f"count not followed by '~' at index {i}")
        if j + 1 >= n:
            raise ValueError(f"missing character after run at index {i}")
        out.append(t[j + 1] * count)
        i = j + 2
    return "".join(out)
