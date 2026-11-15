"""Run-length encoding with a tilde escape character. See spec.md."""

from itertools import groupby
from typing import Tuple

ESCAPE = "~"
RUN_THRESHOLD = 4


def _encode_run(c: str, n: int) -> str:
    """Encode a maximal run of n copies of the character c."""
    if n >= RUN_THRESHOLD:
        return f"{ESCAPE}{n}{ESCAPE}{c}"
    if c == ESCAPE:
        return ESCAPE * 2 * n
    return c * n


def encode(s: str) -> str:
    """Run-length encode s. See spec.md."""
    return "".join(
        _encode_run(c, len(list(group))) for c, group in groupby(s)
    )


def _is_digit(ch: str) -> bool:
    """True for the ASCII decimal digits 0-9."""
    return "0" <= ch <= "9"


def _read_run(t: str, i: int) -> Tuple[str, int]:
    """Read a run starting at t[i] == '~' followed by a digit.

    Returns the expanded run and the index just past it.
    """
    end = i + 1
    while end < len(t) and _is_digit(t[end]):
        end += 1
    digits = t[i + 1:end]
    if digits[0] == "0":
        raise ValueError("count has a leading zero")
    count = int(digits)
    if count < RUN_THRESHOLD:
        raise ValueError("count is below the minimum run length")
    if end >= len(t) or t[end] != ESCAPE:
        raise ValueError("count is not followed by '~'")
    if end + 1 >= len(t):
        raise ValueError("missing character after the run count")
    return t[end + 1] * count, end + 2


def decode(t: str) -> str:
    """Decode an encoded string. See spec.md."""
    out = []
    i = 0
    while i < len(t):
        ch = t[i]
        if ch != ESCAPE:
            out.append(ch)
            i += 1
            continue
        if i + 1 >= len(t):
            raise ValueError("'~' at the end of the text")
        nxt = t[i + 1]
        if nxt == ESCAPE:
            out.append(ESCAPE)
            i += 2
        elif _is_digit(nxt):
            run, i = _read_run(t, i)
            out.append(run)
        else:
            raise ValueError("'~' followed by an invalid character")
    return "".join(out)
