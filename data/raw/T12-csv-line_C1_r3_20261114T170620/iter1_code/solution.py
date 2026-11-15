def _parse_field(line: str, start: int, sep: str) -> tuple[str, int]:
    """Parse one field beginning at ``start``.

    Returns the field value and the index of the separator that ends it
    (or ``len(line)`` if the field runs to the end of the line).
    """
    n = len(line)
    if start < n and line[start] == '"':
        # Quoted field: ends at the first lone quote; "" stands for one quote.
        buf = []
        i = start + 1
        while True:
            if i >= n:
                raise ValueError("unclosed quoted field")
            c = line[i]
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                i += 1  # consume closing quote
                break
            buf.append(c)
            i += 1
        if i < n and line[i] != sep:
            raise ValueError("unexpected character after closing quote")
        return "".join(buf), i

    # Unquoted field: runs up to the next separator or end of line.
    i = start
    while i < n and line[i] != sep:
        c = line[i]
        if c == '"':
            raise ValueError("quote inside unquoted field")
        if c in "\r\n":
            raise ValueError("line break outside quoted field")
        i += 1
    return line[start:i], i


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str):
        raise TypeError("line must be a str")
    if not isinstance(sep, str):
        raise TypeError("sep must be a str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than quote, CR or LF")

    fields = []
    pos = 0
    while True:
        field, pos = _parse_field(line, pos, sep)
        fields.append(field)
        if pos >= len(line):
            break
        pos += 1  # skip the separator
    return fields
