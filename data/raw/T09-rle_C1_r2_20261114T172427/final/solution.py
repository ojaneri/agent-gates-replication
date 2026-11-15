"""Run-length encoding with a '~' escape character. See spec.md."""

ESCAPE = "~"
MIN_RUN = 4


def _is_ascii_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


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
        count = j - i
        if count >= MIN_RUN:
            out.append(f"{ESCAPE}{count}{ESCAPE}{c}")
        elif c == ESCAPE:
            out.append(ESCAPE * 2 * count)
        else:
            out.append(c * count)
        i = j
    return "".join(out)


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    n = len(t)
    while i < n:
        ch = t[i]
        if ch != ESCAPE:
            out.append(ch)
            i += 1
            continue

        # ch is '~': it must be followed by something.
        if i + 1 >= n:
            raise ValueError(f"dangling '~' at position {i}")
        nxt = t[i + 1]

        if nxt == ESCAPE:
            # "~~" stands for a single '~'.
            out.append(ESCAPE)
            i += 2
            continue

        if not _is_ascii_digit(nxt):
            raise ValueError(f"unexpected character {nxt!r} after '~' at position {i}")

        # Run form: '~' digits '~' c
        j = i + 1
        while j < n and _is_ascii_digit(t[j]):
            j += 1
        digits = t[i + 1:j]
        if digits[0] == "0":
            raise ValueError(f"count with leading zero at position {i}")
        count = int(digits)
        if count < MIN_RUN:
            raise ValueError(f"run count {count} below {MIN_RUN} at position {i}")
        if j >= n or t[j] != ESCAPE:
            raise ValueError(f"count not followed by '~' at position {i}")
        if j + 1 >= n:
            raise ValueError(f"missing run character at end of text")
        out.append(t[j + 1] * count)
        i = j + 2

    return "".join(out)
