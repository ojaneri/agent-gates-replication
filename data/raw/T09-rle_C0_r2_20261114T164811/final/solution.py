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
        else:
            out.append((c * 2 if c == "~" else c) * k if c != "~" else "~~" * k)
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
        d = t[i]
        if d == "~":
            out.append("~")
            i += 1
            continue
        if not ("0" <= d <= "9"):
            raise ValueError("bad escape")
        j = i
        while j < n and "0" <= t[j] <= "9":
            j += 1
        digits = t[i:j]
        if len(digits) > 1 and digits[0] == "0" or digits[0] == "0":
            raise ValueError("leading zero")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by ~")
        count = int(digits)
        if count < 4:
            raise ValueError("count too small")
        if j + 1 >= n:
            raise ValueError("missing character")
        out.append(t[j + 1] * count)
        i = j + 2
    return "".join(out)
