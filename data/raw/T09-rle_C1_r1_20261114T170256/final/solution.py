"""Run-length encoding with an escape character. See spec.md."""

_DIGITS = "0123456789"
_MIN_RUN = 4


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        j = i + 1
        while j < n and s[j] == c:
            j += 1
        run = j - i
        if run >= _MIN_RUN:
            out.append(f"~{run}~{c}")
        elif c == "~":
            out.append("~~" * run)
        else:
            out.append(c * run)
        i = j
    return "".join(out)


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
        if i + 1 >= n:
            raise ValueError("dangling '~' at end of text")
        nxt = t[i + 1]
        if nxt == "~":
            out.append("~")
            i += 2
            continue
        if nxt not in _DIGITS:
            raise ValueError(f"unexpected character {nxt!r} after '~'")
        if nxt == "0":
            raise ValueError("count has a leading zero")
        j = i + 1
        while j < n and t[j] in _DIGITS:
            j += 1
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by '~'")
        count = int(t[i + 1:j])
        if count < _MIN_RUN:
            raise ValueError(f"count {count} is below {_MIN_RUN}")
        if j + 1 >= n:
            raise ValueError("missing character after run marker")
        out.append(t[j + 1] * count)
        i = j + 2
    return "".join(out)
