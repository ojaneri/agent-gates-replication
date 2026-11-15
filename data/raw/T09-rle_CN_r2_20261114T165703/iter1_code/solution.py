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
    digits = "0123456789"
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
        if c not in digits:
            raise ValueError("invalid escape")
        j = i
        while j < n and t[j] in digits:
            j += 1
        num = t[i:j]
        if num[0] == "0":
            raise ValueError("leading zero")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by ~")
        if int(num) < 4:
            raise ValueError("count too small")
        if j + 1 >= n:
            raise ValueError("missing character")
        out.append(t[j + 1] * int(num))
        i = j + 2
    return "".join(out)
