MIN_LEN = 12
MAX_LEN = 64


def _is_lower(c: str) -> bool:
    return "a" <= c <= "z"


def _is_upper(c: str) -> bool:
    return "A" <= c <= "Z"


def _is_digit(c: str) -> bool:
    return "0" <= c <= "9"


def _classes(password: str) -> int:
    lower = any(_is_lower(c) for c in password)
    upper = any(_is_upper(c) for c in password)
    digit = any(_is_digit(c) for c in password)
    other = any(not (_is_lower(c) or _is_upper(c) or _is_digit(c)) for c in password)
    return sum([lower, upper, digit, other])


def _has_repeat(password: str) -> bool:
    return any(password[i] == password[i + 1] == password[i + 2] for i in range(len(password) - 2))


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be strings")
    out = []
    if not MIN_LEN <= len(password) <= MAX_LEN:
        out.append("LENGTH")
    if _classes(password) < 3:
        out.append("CLASSES")
    if len(username) >= 3 and username.lower() in password.lower():
        out.append("USERNAME")
    if _has_repeat(password):
        out.append("REPEAT")
    if password.lower() in {b.lower() for b in blocklist}:
        out.append("BLOCKLIST")
    return out
