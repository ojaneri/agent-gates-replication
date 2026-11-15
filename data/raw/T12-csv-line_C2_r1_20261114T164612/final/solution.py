_FORBIDDEN_SEPARATORS = ('"', "\r", "\n")


def _check_args(line, sep):
    """Validate the arguments of parse_line, raising TypeError or ValueError."""
    if not isinstance(line, str):
        raise TypeError("line must be a str")
    if not isinstance(sep, str):
        raise TypeError("sep must be a str")
    if len(sep) != 1 or sep in _FORBIDDEN_SEPARATORS:
        raise ValueError("sep must be one character other than '\"', CR or LF")


def _read_quoted(line, start, sep):
    """Read a quoted field whose body starts at index `start`.

    Returns the decoded value and the index just after the closing quote.
    """
    chars = []
    i = start
    n = len(line)
    while i < n:
        c = line[i]
        if c == '"':
            if i + 1 < n and line[i + 1] == '"':
                chars.append('"')
                i += 2
                continue
            after = i + 1
            if after < n and line[after] != sep:
                raise ValueError("unexpected character after closing quote")
            return "".join(chars), after
        chars.append(c)
        i += 1
    raise ValueError("unterminated quoted field")


def _read_plain(line, start, sep):
    """Read an unquoted field starting at `start`.

    Returns the value and the index of the separator (or len(line)).
    """
    i = start
    while i < len(line) and line[i] != sep:
        if line[i] in _FORBIDDEN_SEPARATORS:
            raise ValueError("quote or line break outside a quoted field")
        i += 1
    return line[start:i], i


def parse_line(line: str, sep: str = ",") -> list[str]:
    """Split one delimited line into fields. See spec.md."""
    _check_args(line, sep)
    fields = []
    n = len(line)
    pos = 0
    while True:
        if pos < n and line[pos] == '"':
            value, pos = _read_quoted(line, pos + 1, sep)
        else:
            value, pos = _read_plain(line, pos, sep)
        fields.append(value)
        if pos >= n:
            return fields
        pos += 1  # skip the separator; another field follows
