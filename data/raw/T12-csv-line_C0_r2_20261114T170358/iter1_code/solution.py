def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str):
        raise TypeError("line must be a str")
    if not isinstance(sep, str):
        raise TypeError("sep must be a str")
    if len(sep) != 1:
        raise ValueError("sep must be exactly one character")
    if sep in ('"', "\r", "\n"):
        raise ValueError("sep must not be a double quote, CR or LF")

    fields: list[str] = []
    n = len(line)
    i = 0
    while True:
        if i < n and line[i] == '"':
            # Quoted field: ends at the first undoubled quote.
            i += 1
            buf: list[str] = []
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
            fields.append("".join(buf))
        else:
            # Unquoted field: runs to the next separator (or end of line).
            start = i
            while i < n and line[i] != sep:
                c = line[i]
                if c in ('"', "\r", "\n"):
                    raise ValueError(f"illegal character {c!r} in unquoted field")
                i += 1
            fields.append(line[start:i])

        if i < n:  # line[i] == sep; move past it and parse the next field
            i += 1
        else:
            break
    return fields
