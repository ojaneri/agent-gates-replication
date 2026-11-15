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
            out.append("~%d~%s" % (run, c))
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
        c = t[i]
        if c != "~":
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= n:
            raise ValueError("dangling ~")
        c = t[i]
        if c == "~":
            out.append("~")
            i += 1
            continue
        if c not in _DIGITS:
            raise ValueError("invalid escape")
        if c == "0":
            raise ValueError("leading zero or zero count")
        j = i
        while j < n and t[j] in _DIGITS:
            j += 1
        count = int(t[i:j])
        if count < 4:
            raise ValueError("count too small")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by ~")
        j += 1
        if j >= n:
            raise ValueError("missing character")
        out.append(t[j] * count)
        i = j + 1
    return "".join(out)
