def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        j = i
        while j < n and s[j] == c:
            j += 1
        run = j - i
        if run >= 4:
            out.append(f"~{run}~{c}")
        elif c == "~":
            out.append("~~" * run)
        else:
            out.append(c * run)
        i = j
    return "".join(out)


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


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

        # ch is '~'; it must be followed by something.
        if i + 1 >= n:
            raise ValueError("'~' at end of text")
        nxt = t[i + 1]

        if nxt == "~":
            out.append("~")
            i += 2
            continue

        if not _is_digit(nxt):
            raise ValueError(f"unexpected character {nxt!r} after '~'")

        j = i + 1
        while j < n and _is_digit(t[j]):
            j += 1
        digits = t[i + 1:j]
        if digits[0] == "0":
            raise ValueError("count has leading zeros")
        count = int(digits)
        if count < 4:
            raise ValueError(f"count {count} is below 4")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by '~'")
        if j + 1 >= n:
            raise ValueError("missing character after run marker")
        c = t[j + 1]
        out.append(c * count)
        i = j + 2

    return "".join(out)
