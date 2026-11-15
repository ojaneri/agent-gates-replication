def _check(line, sep):
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in '"\r\n':
        raise ValueError("invalid separator")


def _plain(line, i, sep):
    j = i
    n = len(line)
    while j < n and line[j] != sep:
        if line[j] in '"\r\n':
            raise ValueError("illegal character in unquoted field")
        j += 1
    return line[i:j], j


def _quoted(line, i, sep):
    buf = []
    n = len(line)
    while i < n:
        c = line[i]
        if c != '"':
            buf.append(c)
            i += 1
        elif line[i + 1:i + 2] == '"':
            buf.append('"')
            i += 2
        else:
            i += 1
            if i < n and line[i] != sep:
                raise ValueError("garbage after closing quote")
            return "".join(buf), i
    raise ValueError("unterminated quoted field")


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    _check(line, sep)
    fields = []
    i = 0
    while True:
        if line.startswith('"', i):
            val, i = _quoted(line, i + 1, sep)
        else:
            val, i = _plain(line, i, sep)
        fields.append(val)
        if i >= len(line):
            return fields
        i += 1
