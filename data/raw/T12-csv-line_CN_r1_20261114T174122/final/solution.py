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
            j = i + 1
            buf: list[str] = []
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
            i = j
        else:
            # Unquoted field.
            j = i
            while j < n and line[j] != sep:
                c = line[j]
                if c in ('"', "\r", "\n"):
                    raise ValueError(f"illegal character {c!r} in unquoted field")
                j += 1
            fields.append(line[i:j])
            i = j

        if i < n:
            # line[i] is sep; a field follows it (possibly empty).
            i += 1
        else:
            break
    return fields
