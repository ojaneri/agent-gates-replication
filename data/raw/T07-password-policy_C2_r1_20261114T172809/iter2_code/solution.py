"""Password policy check. See spec.md."""

_LOWER, _UPPER, _DIGIT, _OTHER = 0, 1, 2, 3


def _class_of(char: str) -> int:
    """Return the character class index of a single character."""
    if "a" <= char <= "z":
        return _LOWER
    if "A" <= char <= "Z":
        return _UPPER
    if "0" <= char <= "9":
        return _DIGIT
    return _OTHER


def _count_classes(password: str) -> int:
    """Return how many distinct character classes the password uses."""
    return len({_class_of(char) for char in password})


def _has_triple_repeat(password: str) -> bool:
    """Return True if the same character appears 3 times in a row."""
    return any(
        first == second == third
        for first, second, third in zip(password, password[1:], password[2:])
    )


def _contains_username(password: str, username: str) -> bool:
    """Return True if a username of 3+ characters appears in the password (case-insensitive)."""
    if len(username) < 3:
        return False
    return username.lower() in password.lower()


def _is_blocklisted(password: str, blocklist: set[str]) -> bool:
    """Return True if the lowercased password equals a lowercased blocklist entry."""
    lowered = password.lower()
    return any(lowered == entry.lower() for entry in blocklist)


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    violations = []
    if not 12 <= len(password) <= 64:
        violations.append("LENGTH")
    if _count_classes(password) < 3:
        violations.append("CLASSES")
    if _contains_username(password, username):
        violations.append("USERNAME")
    if _has_triple_repeat(password):
        violations.append("REPEAT")
    if _is_blocklisted(password, blocklist):
        violations.append("BLOCKLIST")
    return violations
