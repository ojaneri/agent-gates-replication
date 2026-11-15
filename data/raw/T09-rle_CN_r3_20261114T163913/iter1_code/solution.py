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
            out.append("~" + str(k) + "~" + c)
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
    digits = "0123456789"
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
        if d not in digits:
            raise ValueError("invalid escape")
        j = i
        while j < n and t[j] in digits:
            j += 1
        num = t[i:j]
        if len(num) > 1 and num[0] == "0" or num[0] == "0":
            raise ValueError("leading zero")
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by ~")
        count = int(num)
        if count < 4:
            raise ValueError("count too small")
        j += 1
        if j >= n:
            raise ValueError("missing character")
        out.append(t[j] * count)
        i = j + 1
    return "".join(out)
