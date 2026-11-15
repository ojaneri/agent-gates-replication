def _has_lower(ch: str) -> bool:
    return "a" <= ch <= "z"


def _has_upper(ch: str) -> bool:
    return "A" <= ch <= "Z"


def _has_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations: list[str] = []

    # LENGTH: 12..64 characters inclusive.
    if not (12 <= len(password) <= 64):
        violations.append("LENGTH")

    # CLASSES: at least 3 of 4 character classes present.
    has_lower = any(_has_lower(c) for c in password)
    has_upper = any(_has_upper(c) for c in password)
    has_digit = any(_has_digit(c) for c in password)
    has_other = any(
        not (_has_lower(c) or _has_upper(c) or _has_digit(c)) for c in password
    )
    if sum((has_lower, has_upper, has_digit, has_other)) < 3:
        violations.append("CLASSES")

    # USERNAME: username (>= 3 chars) appears in password, case-insensitively.
    lowered_password = password.lower()
    lowered_username = username.lower()
    if len(username) >= 3 and lowered_username in lowered_password:
        violations.append("USERNAME")

    # REPEAT: same character three or more times in a row (case-sensitive).
    run = 0
    previous = None
    repeat = False
    for c in password:
        if c == previous:
            run += 1
        else:
            run = 1
            previous = c
        if run >= 3:
            repeat = True
            break
    if repeat:
        violations.append("REPEAT")

    # BLOCKLIST: lowercased password equals a lowercased blocklist entry.
    lowered_blocklist = {entry.lower() for entry in blocklist}
    if lowered_password in lowered_blocklist:
        violations.append("BLOCKLIST")

    return violations
