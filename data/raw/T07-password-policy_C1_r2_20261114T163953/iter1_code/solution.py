def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters inclusive.
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of 4 ASCII-based classes present.
    has_lower = any("a" <= c <= "z" for c in password)
    has_upper = any("A" <= c <= "Z" for c in password)
    has_digit = any("0" <= c <= "9" for c in password)
    has_other = any(
        not (("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9"))
        for c in password
    )
    if sum((has_lower, has_upper, has_digit, has_other)) < 3:
        violations.append("CLASSES")

    # USERNAME: username (length >= 3) must not appear in the password, case-insensitively.
    lowered_password = password.lower()
    lowered_username = username.lower()
    if len(username) >= 3 and lowered_username in lowered_password:
        violations.append("USERNAME")

    # REPEAT: the same character 3+ times in a row (case-sensitive).
    if any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    ):
        violations.append("REPEAT")

    # BLOCKLIST: equality only, after lowercasing both sides.
    if any(lowered_password == entry.lower() for entry in blocklist):
        violations.append("BLOCKLIST")

    return violations
