import string

_ALNUM = string.ascii_letters + string.digits


def _bad_length(password: str, username: str, blocklist: set[str]) -> bool:
    return not 12 <= len(password) <= 64


def _bad_classes(password: str, username: str, blocklist: set[str]) -> bool:
    count = sum(
        any(c in group for c in password)
        for group in (string.ascii_lowercase, string.ascii_uppercase, string.digits)
    )
    count += any(c not in _ALNUM for c in password)
    return count < 3


def _bad_username(password: str, username: str, blocklist: set[str]) -> bool:
    return len(username) >= 3 and username.lower() in password.lower()


def _bad_repeat(password: str, username: str, blocklist: set[str]) -> bool:
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def _bad_blocklist(password: str, username: str, blocklist: set[str]) -> bool:
    low = password.lower()
    return any(low == entry.lower() for entry in blocklist)


_RULES = (
    ("LENGTH", _bad_length),
    ("CLASSES", _bad_classes),
    ("USERNAME", _bad_username),
    ("REPEAT", _bad_repeat),
    ("BLOCKLIST", _bad_blocklist),
)


def _validate(password: object, username: object) -> None:
    if not (isinstance(password, str) and isinstance(username, str)):
        raise TypeError("password and username must be str")


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    _validate(password, username)
    return [code for code, bad in _RULES if bad(password, username, blocklist)]
