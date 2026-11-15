def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("invalid separator")

    fields = []
    n = len(line)
    i = 0
    while True:
        if i < n and line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                c = line[i]
                if c == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(c)
                i += 1
            fields.append("".join(buf))
            if i >= n:
                return fields
            if line[i] != sep:
                raise ValueError("unexpected character after closing quote")
            i += 1
        else:
            start = i
            while i < n and line[i] != sep:
                if line[i] in ('"', "\r", "\n"):
                    raise ValueError("invalid character in unquoted field")
                i += 1
            fields.append(line[start:i])
            if i >= n:
                return fields
            i += 1
