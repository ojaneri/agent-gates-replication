def _read_quoted(line: str, start: int, sep: str) -> tuple[str, int]:
    """Read a quoted field whose opening quote is at ``start``.

    Returns the unquoted value and the index just past the closing quote.
    """
    n = len(line)
    buf = []
    j = start + 1
    while True:
        if j >= n:
            raise ValueError("quoted field has no closing quote")
        c = line[j]
        if c == '"':
            if j + 1 < n and line[j + 1] == '"':
                buf.append('"')
                j += 2
                continue
            j += 1
            break
        buf.append(c)
        j += 1
    if j < n and line[j] != sep:
        raise ValueError("unexpected character after closing quote")
    return "".join(buf), j


def _read_plain(line: str, start: int, sep: str) -> tuple[str, int]:
    """Read an unquoted field starting at ``start``.

    Returns the field text and the index of the separator that ends it
    (or the length of the line).
    """
    n = len(line)
    j = start
    while j < n and line[j] != sep:
        if line[j] in ('"', "\r", "\n"):
            raise ValueError("illegal character in unquoted field")
        j += 1
    return line[start:j], j


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than quote, CR or LF")

    fields = []
    i = 0
    while True:
        if i < len(line) and line[i] == '"':
            value, j = _read_quoted(line, i, sep)
        else:
            value, j = _read_plain(line, i, sep)
        fields.append(value)
        if j >= len(line):
            return fields
        i = j + 1
