def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters inclusive.
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of 4 character classes present.
    has_lower = any("a" <= ch <= "z" for ch in password)
    has_upper = any("A" <= ch <= "Z" for ch in password)
    has_digit = any("0" <= ch <= "9" for ch in password)
    has_other = any(
        not (("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9"))
        for ch in password
    )
    if has_lower + has_upper + has_digit + has_other < 3:
        violations.append("CLASSES")

    # USERNAME: username (>= 3 chars) appears inside password, case-insensitively.
    lowered_password = password.lower()
    lowered_username = username.lower()
    if len(username) >= 3 and lowered_username in lowered_password:
        violations.append("USERNAME")

    # REPEAT: same character three or more times in a row (case-sensitive).
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            violations.append("REPEAT")
            break

    # BLOCKLIST: lowercased password equals a lowercased blocklist entry.
    lowered_blocklist = {entry.lower() for entry in blocklist}
    if lowered_password in lowered_blocklist:
        violations.append("BLOCKLIST")

    return violations
