import string


_LOWER = frozenset(string.ascii_lowercase)
_UPPER = frozenset(string.ascii_uppercase)
_DIGIT = frozenset(string.digits)


def _char_class(ch: str) -> int:
    if ch in _LOWER:
        return 0
    if ch in _UPPER:
        return 1
    if ch in _DIGIT:
        return 2
    return 3


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of the 4 classes present
    classes = {_char_class(ch) for ch in password}
    if len(classes) < 3:
        violations.append("CLASSES")

    # USERNAME: username of 3+ chars appears inside password (case-insensitive)
    lowered_password = password.lower()
    if len(username) >= 3 and username.lower() in lowered_password:
        violations.append("USERNAME")

    # REPEAT: same character 3+ times in a row (case-sensitive)
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            violations.append("REPEAT")
            break

    # BLOCKLIST: equality only, after lower()
    lowered_blocklist = {entry.lower() for entry in blocklist}
    if lowered_password in lowered_blocklist:
        violations.append("BLOCKLIST")

    return violations
