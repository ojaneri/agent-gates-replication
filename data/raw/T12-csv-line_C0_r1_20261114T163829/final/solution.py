def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str):
        raise TypeError("line must be a str")
    if not isinstance(sep, str):
        raise TypeError("sep must be a str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than '\"', '\\r' or '\\n'")

    fields: list[str] = []
    n = len(line)
    i = 0
    while True:
        if i < n and line[i] == '"':
            # Quoted field: runs until an undoubled quote.
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
                    i += 1  # closing quote
                    break
                buf.append(c)
                i += 1
            if i < n and line[i] != sep:
                raise ValueError("unexpected character after closing quote")
            fields.append("".join(buf))
        else:
            # Unquoted field: runs until the separator or end of line.
            j = i
            while j < n and line[j] != sep:
                c = line[j]
                if c == '"':
                    raise ValueError("quote inside unquoted field")
                if c in "\r\n":
                    raise ValueError("line break outside quoted field")
                j += 1
            fields.append(line[i:j])
            i = j

        if i < n:
            # line[i] is the separator; a field follows it (possibly empty).
            i += 1
        else:
            break
    return fields
