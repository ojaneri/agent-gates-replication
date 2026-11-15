def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    out = []
    if not 12 <= len(password) <= 64:
        out.append("LENGTH")
    classes = [
        any("a" <= c <= "z" for c in password),
        any("A" <= c <= "Z" for c in password),
        any("0" <= c <= "9" for c in password),
        any(not c.isascii() or not c.isalnum() for c in password),
    ]
    if sum(classes) < 3:
        out.append("CLASSES")
    if len(username) >= 3 and username.lower() in password.lower():
        out.append("USERNAME")
    if any(password[i] == password[i + 1] == password[i + 2]
           for i in range(len(password) - 2)):
        out.append("REPEAT")
    low = password.lower()
    if any(low == b.lower() for b in blocklist):
        out.append("BLOCKLIST")
    return out
