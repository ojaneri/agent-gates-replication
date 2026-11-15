def _is_lower(ch: str) -> bool:
    return "a" <= ch <= "z"


def _is_upper(ch: str) -> bool:
    return "A" <= ch <= "Z"


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _class_count(password: str) -> int:
    """Count how many of the 4 character classes appear in the password."""
    classes = set()
    for ch in password:
        if _is_lower(ch):
            classes.add("lower")
        elif _is_upper(ch):
            classes.add("upper")
        elif _is_digit(ch):
            classes.add("digit")
        else:
            classes.add("other")
    return len(classes)


def _has_repeat(password: str) -> bool:
    """True if the same character appears 3 or more times in a row (case-sensitive)."""
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def _uses_username(password: str, username: str) -> bool:
    return len(username) >= 3 and username.lower() in password.lower()


def _in_blocklist(password: str, blocklist: set[str]) -> bool:
    lowered = password.lower()
    return any(lowered == entry.lower() for entry in blocklist)


def _require_strings(password: object, username: object) -> None:
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    _require_strings(password, username)
    checks = (
        ("LENGTH", not 12 <= len(password) <= 64),
        ("CLASSES", _class_count(password) < 3),
        ("USERNAME", _uses_username(password, username)),
        ("REPEAT", _has_repeat(password)),
        ("BLOCKLIST", _in_blocklist(password, blocklist)),
    )
    return [code for code, violated in checks if violated]
