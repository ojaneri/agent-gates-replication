def _class_of(ch: str) -> int:
    if "a" <= ch <= "z":
        return 0
    if "A" <= ch <= "Z":
        return 1
    if "0" <= ch <= "9":
        return 2
    return 3


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
        ("CLASSES", len({_class_of(c) for c in password}) < 3),
        ("USERNAME", _has_username(password, username)),
        ("REPEAT", _has_repeat(password)),
        ("BLOCKLIST", _is_blocked(password, blocklist)),
    ]
    return [code for code, bad in checks if bad]
