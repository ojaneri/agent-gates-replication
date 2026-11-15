import string

_LOWER = frozenset(string.ascii_lowercase)
_UPPER = frozenset(string.ascii_uppercase)
_DIGITS = frozenset(string.digits)
_ALNUM = _LOWER | _UPPER | _DIGITS


def _has_three_classes(password: str) -> bool:
    """Return True if password has characters from at least 3 of the 4 classes."""
    found = sum(any(ch in chars for ch in password) for chars in (_LOWER, _UPPER, _DIGITS))
    found += any(ch not in _ALNUM for ch in password)
    return found >= 3


def _has_triple_repeat(password: str) -> bool:
    """Return True if the same character appears 3 or more times in a row."""
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not (isinstance(password, str) and isinstance(username, str)):
        raise TypeError("password and username must be str")

    lower_password = password.lower()
    lower_username = username.lower()
    lower_blocklist = {entry.lower() for entry in blocklist}
    checks = (
        (not 12 <= len(password) <= 64, "LENGTH"),
        (not _has_three_classes(password), "CLASSES"),
        (len(username) >= 3 and lower_username in lower_password, "USERNAME"),
        (_has_triple_repeat(password), "REPEAT"),
        (lower_password in lower_blocklist, "BLOCKLIST"),
    )
    return [code for failed, code in checks if failed]
