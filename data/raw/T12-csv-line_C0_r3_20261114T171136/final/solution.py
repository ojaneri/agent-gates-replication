def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than '\"', '\\r' or '\\n'")

    n = len(line)
    fields: list[str] = []
    pos = 0
    while True:
        if pos < n and line[pos] == '"':
            # Quoted field.
            buf: list[str] = []
            j = pos + 1
            while True:
                if j >= n:
                    raise ValueError("unclosed quoted field")
                c = line[j]
                if c == '"':
                    if j + 1 < n and line[j + 1] == '"':
                        buf.append('"')
                        j += 2
                        continue
                    j += 1  # closing quote
                    break
                buf.append(c)
                j += 1
            if j < n and line[j] != sep:
                raise ValueError("unexpected character after closing quote")
            fields.append("".join(buf))
            pos = j
        else:
            # Unquoted field.
            j = pos
            while j < n and line[j] != sep:
                c = line[j]
                if c == '"':
                    raise ValueError("'\"' inside unquoted field")
                if c in ("\r", "\n"):
                    raise ValueError("line break outside quoted field")
                j += 1
            fields.append(line[pos:j])
            pos = j

        if pos >= n:
            break
        pos += 1  # skip separator
    return fields
