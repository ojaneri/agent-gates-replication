_DIGITS = "0123456789"


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
            out.append("~" + str(run) + "~" + c)
        else:
            piece = "~~" if c == "~" else c
            out.append(piece * run)
        i = j
    return "".join(out)


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c != "~":
            out.append(c)
            i += 1
            continue

        # c is '~'; a tilde must be followed by something.
        if i + 1 >= n:
            raise ValueError("dangling '~' at end of text")
        nxt = t[i + 1]

        if nxt == "~":
            out.append("~")
            i += 2
            continue

        if nxt not in _DIGITS:
            raise ValueError("'~' followed by invalid character %r" % nxt)

        # Read the decimal count.
        j = i + 1
        while j < n and t[j] in _DIGITS:
            j += 1
        digits = t[i + 1:j]
        if digits[0] == "0":
            raise ValueError("count has leading zero: %r" % digits)
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by '~'")
        count = int(digits)
        if count < 4:
            raise ValueError("count below 4: %d" % count)
        if j + 1 >= n:
            raise ValueError("missing character after run count")
        ch = t[j + 1]
        out.append(ch * count)
        i = j + 2

    return "".join(out)
