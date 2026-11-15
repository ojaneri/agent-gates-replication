import string

_LOWER = frozenset(string.ascii_lowercase)
_UPPER = frozenset(string.ascii_uppercase)
_DIGITS = frozenset(string.digits)
_ASCII = _LOWER | _UPPER | _DIGITS


def _bad_length(password, username, blocklist):
    return not 12 <= len(password) <= 64


def _bad_classes(password, username, blocklist):
    chars = set(password)
    present = [
        bool(chars & _LOWER),
        bool(chars & _UPPER),
        bool(chars & _DIGITS),
        bool(chars - _ASCII),
    ]
    return sum(present) < 3


def _bad_username(password, username, blocklist):
    return len(username) >= 3 and username.lower() in password.lower()


def _bad_repeat(password, username, blocklist):
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def _bad_blocklist(password, username, blocklist):
    lowered = password.lower()
    return any(lowered == entry.lower() for entry in blocklist)


_RULES = (
    ("LENGTH", _bad_length),
    ("CLASSES", _bad_classes),
    ("USERNAME", _bad_username),
    ("REPEAT", _bad_repeat),
    ("BLOCKLIST", _bad_blocklist),
)


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    return [code for code, bad in _RULES if bad(password, username, blocklist)]
