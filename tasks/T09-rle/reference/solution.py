ESC = "~"
MIN_RUN = 4
DIGITS = "0123456789"


def encode(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        j = i
        while j < len(s) and s[j] == c:
            j += 1
        n = j - i
        if n >= MIN_RUN:
            out.append(f"{ESC}{n}{ESC}{c}")
        else:
            out.append((ESC + ESC if c == ESC else c) * n)
        i = j
    return "".join(out)


def decode(t: str) -> str:
    out = []
    i = 0
    while i < len(t):
        c = t[i]
        if c != ESC:
            out.append(c)
            i += 1
            continue
        if i + 1 >= len(t):
            raise ValueError("dangling escape at end")
        nxt = t[i + 1]
        if nxt == ESC:
            out.append(ESC)
            i += 2
            continue
        if nxt not in DIGITS:
            raise ValueError("escape must be followed by ~ or a count")
        rest = t[i + 1:]
        k = len(rest) - len(rest.lstrip(DIGITS))
        digits = rest[:k]
        j = i + 1 + k
        if digits[0] == "0":
            raise ValueError("count has leading zeros")
        n = int(digits)
        if n < MIN_RUN:
            raise ValueError("count below minimum run")
        if j >= len(t) or t[j] != ESC:
            raise ValueError("count not followed by escape")
        if j + 1 >= len(t):
            raise ValueError("missing run character")
        out.append(t[j + 1] * n)
        i = j + 2
    return "".join(out)
