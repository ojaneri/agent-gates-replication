import itertools


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    out = []
    for c, group in itertools.groupby(s):
        n = sum(1 for _ in group)
        if n >= 4:
            out.append(f"~{n}~{c}")
        elif c == "~":
            out.append("~~" * n)
        else:
            out.append(c * n)
    return "".join(out)


def _read_count(t: str, i: int):
    """Read a decimal run count starting at t[i].

    Returns (count, index just after the digits).
    """
    start = i
    while i < len(t) and "0" <= t[i] <= "9":
        i += 1
    digits = t[start:i]
    if not digits:
        raise ValueError(f"expected a count at position {start}")
    if digits[0] == "0":
        raise ValueError("count has leading zeros")
    count = int(digits)
    if count < 4:
        raise ValueError(f"count {count} is below 4")
    return count, i


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    n = len(t)
    while i < n:
        if t[i] != "~":
            out.append(t[i])
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("'~' at end of text")
        if t[i + 1] == "~":
            out.append("~")
            i += 2
            continue
        count, j = _read_count(t, i + 1)
        if j >= n or t[j] != "~":
            raise ValueError("count not followed by '~'")
        if j + 1 >= n:
            raise ValueError("missing character after run count")
        out.append(t[j + 1] * count)
        i = j + 2
    return "".join(out)
