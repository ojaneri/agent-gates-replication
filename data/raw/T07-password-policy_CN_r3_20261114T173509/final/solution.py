def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters inclusive.
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of lowercase ASCII, uppercase ASCII, ASCII digits, other.
    has_lower = any("a" <= c <= "z" for c in password)
    has_upper = any("A" <= c <= "Z" for c in password)
    has_digit = any("0" <= c <= "9" for c in password)
    has_other = any(not ("a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9")
                    for c in password)
    if sum([has_lower, has_upper, has_digit, has_other]) < 3:
        violations.append("CLASSES")

    # USERNAME: username of 3+ chars appearing in password (case-insensitive).
    if len(username) >= 3 and username.lower() in password.lower():
        violations.append("USERNAME")

    # REPEAT: same character 3+ times in a row (case-sensitive).
    run = 1
    repeat = False
    for i in range(1, len(password)):
        if password[i] == password[i - 1]:
            run += 1
            if run >= 3:
                repeat = True
                break
        else:
            run = 1
    if repeat:
        violations.append("REPEAT")

    # BLOCKLIST: equality (after lower()) with any blocklist entry.
    lowered = password.lower()
    if any(lowered == entry.lower() for entry in blocklist):
        violations.append("BLOCKLIST")

    return violations
