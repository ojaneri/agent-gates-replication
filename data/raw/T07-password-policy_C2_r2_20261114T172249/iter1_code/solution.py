def _has_three_classes(password: str) -> bool:
    """Return True if password has characters from at least 3 of the 4 classes."""
    has_lower = any("a" <= ch <= "z" for ch in password)
    has_upper = any("A" <= ch <= "Z" for ch in password)
    has_digit = any("0" <= ch <= "9" for ch in password)
    has_other = any(not ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9") for ch in password)
    return [has_lower, has_upper, has_digit, has_other].count(True) >= 3


def _has_triple_repeat(password: str) -> bool:
    """Return True if the same character appears 3 or more times in a row."""
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            return True
    return False


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations = []
    if not 12 <= len(password) <= 64:
        violations.append("LENGTH")
    if not _has_three_classes(password):
        violations.append("CLASSES")
    lower_password = password.lower()
    lower_username = username.lower()
    if len(username) >= 3 and lower_username in lower_password:
        violations.append("USERNAME")
    if _has_triple_repeat(password):
        violations.append("REPEAT")
    lower_blocklist = {entry.lower() for entry in blocklist}
    if lower_password in lower_blocklist:
        violations.append("BLOCKLIST")
    return violations
