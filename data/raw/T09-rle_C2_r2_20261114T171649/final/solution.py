DIGITS = "0123456789"


def _emit(c: str, n: int) -> str:
    if n >= 4:
        return "~" + str(n) + "~" + c
    return c * n if c != "~" else "~~" * n


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(_emit(s[i], j - i))
        i = j
    return "".join(out)


def _read_count(t: str, i: int):
    j = i
    while j < len(t) and t[j] in DIGITS:
        j += 1
    digits = t[i:j]
    if not digits or digits[0] == "0" or int(digits) < 4:
        raise ValueError("invalid count")
    if j >= len(t) or t[j] != "~" or j + 1 >= len(t):
        raise ValueError("malformed run")
    return int(digits), t[j + 1], j + 2


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    while i < len(t):
        c = t[i]
        if c != "~":
            out.append(c)
            i += 1
        elif i + 1 >= len(t):
            raise ValueError("dangling escape")
        elif t[i + 1] == "~":
            out.append("~")
            i += 2
        else:
            n, ch, i = _read_count(t, i + 1)
            out.append(ch * n)
    return "".join(out)
