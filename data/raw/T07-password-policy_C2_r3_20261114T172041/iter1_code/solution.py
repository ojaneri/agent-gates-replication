def _char_class(ch: str) -> int:
    if "a" <= ch <= "z":
        return 0
    if "A" <= ch <= "Z":
        return 1
    if "0" <= ch <= "9":
        return 2
    return 3


def _has_repeat(password: str) -> bool:
    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            return True
    return False


def _in_blocklist(password: str, blocklist: set[str]) -> bool:
    low = password.lower()
    return any(low == entry.lower() for entry in blocklist)


def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    out = []
    if not 12 <= len(password) <= 64:
        out.append("LENGTH")
    if len({_char_class(c) for c in password}) < 3:
        out.append("CLASSES")
    if len(username) >= 3 and username.lower() in password.lower():
        out.append("USERNAME")
    if _has_repeat(password):
        out.append("REPEAT")
    if _in_blocklist(password, blocklist):
        out.append("BLOCKLIST")
    return out
