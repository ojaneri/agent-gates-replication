QUOTE = '"'
LINE_BREAKS = "\r\n"


def parse_line(line: str, sep: str = ",") -> list[str]:
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep == QUOTE or sep in LINE_BREAKS:
        raise ValueError("invalid separator")
    fields = []
    n = len(line)
    i = 0
    while True:
        field = []
        if i < n and line[i] == QUOTE:
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                c = line[i]
                if c == QUOTE:
                    if line[i + 1:i + 2] == QUOTE:
                        field.append(QUOTE)
                        i += 2
                        continue
                    i += 1
                    break
                field.append(c)
                i += 1
            if i < n and line[i] != sep:
                raise ValueError("text after closing quote")
        else:
            while i < n and line[i] != sep:
                c = line[i]
                if c == QUOTE:
                    raise ValueError("quote inside unquoted field")
                if c in LINE_BREAKS:
                    raise ValueError("line break outside quotes")
                field.append(c)
                i += 1
        fields.append("".join(field))
        if i >= n:
            return fields
        i += 1
