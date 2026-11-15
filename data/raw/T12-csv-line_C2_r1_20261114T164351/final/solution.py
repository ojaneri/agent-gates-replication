def _read_quoted(line: str, start: int, sep: str) -> tuple[str, int]:
    pos = start + 1
    parts = []
    while True:
        j = line.find('"', pos)
        if j < 0:
            raise ValueError("unterminated quoted field")
        parts.append(line[pos:j])
        if line[j + 1:j + 2] == '"':
            parts.append('"')
            pos = j + 2
            continue
        end = j + 1
        if line[end:end + 1] not in ("", sep):
            raise ValueError("unexpected character after closing quote")
        return "".join(parts), end


def _read_plain(line: str, start: int, sep: str) -> tuple[str, int]:
    end = line.find(sep, start)
    if end < 0:
        end = len(line)
    field = line[start:end]
    if '"' in field or "\r" in field or "\n" in field:
        raise ValueError("illegal character in unquoted field")
    return field, end


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("invalid separator")
    fields = []
    pos = 0
    while True:
        if line[pos:pos + 1] == '"':
            value, pos = _read_quoted(line, pos, sep)
        else:
            value, pos = _read_plain(line, pos, sep)
        fields.append(value)
        if pos >= len(line):
            return fields
        pos += 1
