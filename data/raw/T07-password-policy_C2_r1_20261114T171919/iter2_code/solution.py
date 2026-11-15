import string

_LOWER = frozenset(string.ascii_lowercase)
_UPPER = frozenset(string.ascii_uppercase)
_DIGITS = frozenset(string.digits)
_ASCII_ALNUM = _LOWER | _UPPER | _DIGITS


def _count_classes(password: str) -> int:
    chars = set(password)
    groups = [chars & _LOWER, chars & _UPPER, chars & _DIGITS, chars - _ASCII_ALNUM]
    return sum(1 for g in groups if g)


def _has_repeat(password: str) -> bool:
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def _has_username(password: str, username: str) -> bool:
    return len(username) >= 3 and username.lower() in password.lower()


def _is_blocked(password: str, blocklist: set[str]) -> bool:
    low = password.lower()
    return any(entry.lower() == low for entry in blocklist)


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    checks = [
        ("LENGTH", not 12 <= len(password) <= 64),
        ("CLASSES", _count_classes(password) < 3),
        ("USERNAME", _has_username(password, username)),
        ("REPEAT", _has_repeat(password)),
        ("BLOCKLIST", _is_blocked(password, blocklist)),
    ]
    return [code for code, bad in checks if bad]
