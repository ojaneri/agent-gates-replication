def _quoted(line: str, start: int, sep: str) -> tuple[str, int]:
    """Parse quoted field starting at line[start] == '"'. Return (value, index after it)."""
    parts = []
    pos = start + 1
    while True:
        k = line.find('"', pos)
        if k == -1:
            raise ValueError("unterminated quoted field")
        if line[k + 1:k + 2] == '"':
            parts.append(line[pos:k + 1])
            pos = k + 2
            continue
        parts.append(line[pos:k])
        end = k + 1
        if end < len(line) and line[end] != sep:
            raise ValueError("unexpected character after closing quote")
        return "".join(parts), end


def _plain(line: str, start: int, sep: str) -> tuple[str, int]:
    """Parse unquoted field. Return (value, index of separator or end)."""
    pos = start
    while pos < len(line) and line[pos] != sep:
        if line[pos] in '"\r\n':
            raise ValueError("illegal character in unquoted field")
        pos += 1
    return line[start:pos], pos


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in '"\r\n':
        raise ValueError("invalid separator")
    fields = []
    pos = 0
    while True:
        if line.startswith('"', pos):
            value, pos = _quoted(line, pos, sep)
        else:
            value, pos = _plain(line, pos, sep)
        fields.append(value)
        if pos >= len(line):
            return fields
        pos += 1
