def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters, both ends inclusive.
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of 4 character classes present.
    has_lower = False
    has_upper = False
    has_digit = False
    has_other = False
    for ch in password:
        if "a" <= ch <= "z":
            has_lower = True
        elif "A" <= ch <= "Z":
            has_upper = True
        elif "0" <= ch <= "9":
            has_digit = True
        else:
            has_other = True
    if sum([has_lower, has_upper, has_digit, has_other]) < 3:
        violations.append("CLASSES")

    # USERNAME: username of 3+ chars appears in password (case-insensitive).
    pw_lower = password.lower()
    user_lower = username.lower()
    if len(username) >= 3 and user_lower in pw_lower:
        violations.append("USERNAME")

    # REPEAT: same character 3+ times in a row (case-sensitive).
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            violations.append("REPEAT")
            break

    # BLOCKLIST: lowercased password equals a lowercased blocklist entry.
    lowered_blocklist = {entry.lower() for entry in blocklist}
    if pw_lower in lowered_blocklist:
        violations.append("BLOCKLIST")

    return violations
