def _has_three_classes(password: str) -> bool:
    lower = upper = digit = other = False
    for ch in password:
        if "a" <= ch <= "z":
            lower = True
        elif "A" <= ch <= "Z":
            upper = True
        elif "0" <= ch <= "9":
            digit = True
        else:
            other = True
    return (lower + upper + digit + other) >= 3


def _has_triple_repeat(password: str) -> bool:
    run = 0
    prev = None
    for ch in password:
        if ch == prev:
            run += 1
        else:
            run = 1
            prev = ch
        if run >= 3:
            return True
    return False


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations = []

    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    if not _has_three_classes(password):
        violations.append("CLASSES")

    lowered_password = password.lower()
    lowered_username = username.lower()
    if len(username) >= 3 and lowered_username in lowered_password:
        violations.append("USERNAME")

    if _has_triple_repeat(password):
        violations.append("REPEAT")

    lowered_blocklist = {entry.lower() for entry in blocklist}
    if lowered_password in lowered_blocklist:
        violations.append("BLOCKLIST")

    return violations
