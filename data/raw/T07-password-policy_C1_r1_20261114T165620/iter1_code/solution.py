def _is_lower(c: str) -> bool:
    return "a" <= c <= "z"


def _is_upper(c: str) -> bool:
    return "A" <= c <= "Z"


def _is_digit(c: str) -> bool:
    return "0" <= c <= "9"


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters, both ends inclusive.
    if not 12 <= len(password) <= 64:
        violations.append("LENGTH")

    # CLASSES: at least 3 of 4 character classes present.
    has_lower = any(_is_lower(c) for c in password)
    has_upper = any(_is_upper(c) for c in password)
    has_digit = any(_is_digit(c) for c in password)
    has_other = any(
        not (_is_lower(c) or _is_upper(c) or _is_digit(c)) for c in password
    )
    if sum((has_lower, has_upper, has_digit, has_other)) < 3:
        violations.append("CLASSES")

    lowered_password = password.lower()

    # USERNAME: username (len >= 3) appears inside the password, case-insensitive.
    if len(username) >= 3 and username.lower() in lowered_password:
        violations.append("USERNAME")

    # REPEAT: same character three or more times in a row (case-sensitive).
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            violations.append("REPEAT")
            break

    # BLOCKLIST: equality (case-insensitive) with a blocklist entry.
    if any(lowered_password == entry.lower() for entry in blocklist):
        violations.append("BLOCKLIST")

    return violations
