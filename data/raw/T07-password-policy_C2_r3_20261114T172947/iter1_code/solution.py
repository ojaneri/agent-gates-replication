def _has_repeat(password: str) -> bool:
    """True if the same character appears 3 or more times in a row (case-sensitive)."""
    run = 0
    previous = None
    for ch in password:
        if ch == previous:
            run += 1
        else:
            run = 1
            previous = ch
        if run >= 3:
            return True
    return False


def _class_count(password: str) -> int:
    """Count how many of the 4 character classes appear in the password."""
    has_lower = any("a" <= ch <= "z" for ch in password)
    has_upper = any("A" <= ch <= "Z" for ch in password)
    has_digit = any("0" <= ch <= "9" for ch in password)
    has_other = any(
        not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
        for ch in password
    )
    return sum((has_lower, has_upper, has_digit, has_other))


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    if not 12 <= len(password) <= 64:
        violations.append("LENGTH")

    if _class_count(password) < 3:
        violations.append("CLASSES")

    lowered_password = password.lower()
    if len(username) >= 3 and username.lower() in lowered_password:
        violations.append("USERNAME")

    if _has_repeat(password):
        violations.append("REPEAT")

    if any(lowered_password == entry.lower() for entry in blocklist):
        violations.append("BLOCKLIST")

    return violations
