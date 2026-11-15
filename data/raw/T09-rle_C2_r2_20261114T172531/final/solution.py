"""Run-length encoding with an escape character (~). See spec.md."""

import itertools

MIN_RUN = 4
ESCAPE = "~"


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    parts = []
    for ch, group in itertools.groupby(s):
        n = len(list(group))
        if n >= MIN_RUN:
            parts.append(f"{ESCAPE}{n}{ESCAPE}{ch}")
        elif ch == ESCAPE:
            parts.append(ESCAPE * 2 * n)
        else:
            parts.append(ch * n)
    return "".join(parts)


def _read_count(t: str, i: int) -> tuple:
    """Parse the decimal count starting at index i; return (count, index after it)."""
    j = i
    while j < len(t) and "0" <= t[j] <= "9":
        j += 1
    digits = t[i:j]
    if not digits:
        raise ValueError(f"expected a count after '~' at index {i - 1}")
    if digits[0] == "0":
        raise ValueError(f"count has a leading zero at index {i}")
    count = int(digits)
    if count < MIN_RUN:
        raise ValueError(f"count {count} is below {MIN_RUN}")
    return count, j


def _read_run(t: str, i: int) -> tuple:
    """Read '<count>~<c>' starting at index i (just after the opening '~').

    Return (expanded text, index after the run).
    """
    count, j = _read_count(t, i)
    if j >= len(t) or t[j] != ESCAPE:
        raise ValueError(f"count at index {i} is not followed by '~'")
    j += 1
    if j >= len(t):
        raise ValueError("missing character after run marker")
    return t[j] * count, j + 1


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    while i < len(t):
        if t[i] != ESCAPE:
            out.append(t[i])
            i += 1
        elif i + 1 >= len(t):
            raise ValueError("text ends with '~'")
        elif t[i + 1] == ESCAPE:
            out.append(ESCAPE)
            i += 2
        else:
            text, i = _read_run(t, i + 1)
            out.append(text)
    return "".join(out)
