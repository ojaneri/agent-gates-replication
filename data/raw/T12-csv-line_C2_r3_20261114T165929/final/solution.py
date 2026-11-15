def _check_sep(sep: str) -> None:
    """Raise ValueError unless sep is a single allowed character."""
    if len(sep) != 1 or sep in ('"', "\r", "\n"):
        raise ValueError("sep must be one character other than '\"', '\\r' or '\\n'")


def _read_quoted(line: str, start: int) -> tuple[str, int]:
    """Read a quoted field whose opening quote is at line[start].

    Returns the decoded value and the index just past the closing quote.
    """
    chars = []
    i = start + 1
    n = len(line)
    while i < n:
        c = line[i]
        if c != '"':
            chars.append(c)
            i += 1
        elif i + 1 < n and line[i + 1] == '"':
            chars.append('"')
            i += 2
        else:
            return "".join(chars), i + 1
    raise ValueError("unclosed quoted field")


def _read_unquoted(line: str, start: int, sep: str) -> tuple[str, int]:
    """Read an unquoted field beginning at start.

    Returns the raw text and the index of the separator (or end of line).
    """
    i = start
    while i < len(line) and line[i] != sep:
        if line[i] == '"' or line[i] in "\r\n":
            raise ValueError("invalid character in unquoted field")
        i += 1
    return line[start:i], i


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    if not isinstance(line, str) or not isinstance(sep, str):
        raise TypeError("line and sep must be str")
    _check_sep(sep)

    fields = []
    i = 0
    n = len(line)
    while True:
        if i < n and line[i] == '"':
            field, i = _read_quoted(line, i)
            if i < n and line[i] != sep:
                raise ValueError("unexpected character after closing quote")
        else:
            field, i = _read_unquoted(line, i, sep)
        fields.append(field)
        if i >= n:
            return fields
        i += 1  # skip the separator
