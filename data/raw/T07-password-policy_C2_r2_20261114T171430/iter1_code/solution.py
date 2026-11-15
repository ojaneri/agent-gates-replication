def _char_class(ch: str) -> int:
    if "a" <= ch <= "z":
        return 0
    if "A" <= ch <= "Z":
        return 1
    if "0" <= ch <= "9":
        return 2
    return 3


def _has_repeat(password: str) -> bool:
    return any(
        password[i] == password[i + 1] == password[i + 2]
        for i in range(len(password) - 2)
    )


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    result = []
    if not 12 <= len(password) <= 64:
        result.append("LENGTH")
    if len({_char_class(c) for c in password}) < 3:
        result.append("CLASSES")
    lowered = password.lower()
    user = username.lower()
    if len(username) >= 3 and user in lowered:
        result.append("USERNAME")
    if _has_repeat(password):
        result.append("REPEAT")
    if any(lowered == entry.lower() for entry in blocklist):
        result.append("BLOCKLIST")
    return result
