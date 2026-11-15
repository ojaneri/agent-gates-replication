def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than '\"', '\\r' or '\\n'")

    fields: list[str] = []
    n = len(line)
    i = 0
    while True:
        if i < n and line[i] == '"':
            # Quoted field: ends at the next undoubled quote.
            i += 1
            buf: list[str] = []
            while True:
                if i >= n:
                    raise ValueError("quoted field has no closing quote")
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
            fields.append("".join(buf))
            if i < n and line[i] != sep:
                raise ValueError("unexpected character after closing quote")
        else:
            # Unquoted field: runs until the separator or end of line.
            start = i
            while i < n and line[i] != sep:
                c = line[i]
                if c == '"' or c == "\r" or c == "\n":
                    raise ValueError(f"invalid character {c!r} in unquoted field")
                i += 1
            fields.append(line[start:i])

        if i >= n:
            break
        # line[i] is the separator; skip it and start the next field.
        i += 1

    return fields
