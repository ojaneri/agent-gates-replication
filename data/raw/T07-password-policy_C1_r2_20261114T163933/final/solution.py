def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    out = []
    if not 12 <= len(password) <= 64:
        out.append("LENGTH")
    classes = set()
    for c in password:
        if "a" <= c <= "z":
            classes.add(0)
        elif "A" <= c <= "Z":
            classes.add(1)
        elif "0" <= c <= "9":
            classes.add(2)
        else:
            classes.add(3)
    if len(classes) < 3:
        out.append("CLASSES")
    if len(username) >= 3 and username.lower() in password.lower():
        out.append("USERNAME")
    if any(password[i] == password[i + 1] == password[i + 2] for i in range(len(password) - 2)):
        out.append("REPEAT")
    low = password.lower()
    if any(isinstance(b, str) and b.lower() == low for b in blocklist):
        out.append("BLOCKLIST")
    return out
