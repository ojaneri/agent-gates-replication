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
        k = j - i
        if k >= 4:
            out.append("~%d~%s" % (k, c))
        elif c == "~":
            out.append("~~" * k)
        else:
            out.append(c * k)
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
            raise ValueError("trailing ~")
        c = t[i]
        if c == "~":
            out.append("~")
            i += 1
            continue
        if c not in "0123456789":
            raise ValueError("bad character after ~")
        j = i
        while j < n and t[j] in "0123456789":
            j += 1
        digits = t[i:j]
        if len(digits) > 1 and digits[0] == "0":
            raise ValueError("leading zeros")
        if digits[0] == "0" or int(digits) < 4:
            raise ValueError("count too small")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by ~")
        j += 1
        if j >= n:
            raise ValueError("missing character")
        out.append(t[j] * int(digits))
        i = j + 1
    return "".join(out)
