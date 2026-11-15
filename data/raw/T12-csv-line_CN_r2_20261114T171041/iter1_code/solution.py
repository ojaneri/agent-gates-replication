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
            # Quoted field.
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
            fields.append("".join(buf))
            if i < n:
                if line[i] != sep:
                    raise ValueError("unexpected character after closing quote")
                i += 1  # consume separator; another field follows
                continue
            break
        else:
            # Unquoted field.
            start = i
            while i < n and line[i] != sep:
                c = line[i]
                if c == '"' or c == "\r" or c == "\n":
                    raise ValueError("illegal character in unquoted field")
                i += 1
            fields.append(line[start:i])
            if i < n:
                i += 1  # consume separator; another field follows
                continue
            break
    return fields
