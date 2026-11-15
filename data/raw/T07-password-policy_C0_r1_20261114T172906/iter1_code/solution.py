def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")
    out = []
    if not 12 <= len(password) <= 64:
        out.append("LENGTH")
    classes = [False] * 4
    for ch in password:
        if "a" <= ch <= "z":
            classes[0] = True
        elif "A" <= ch <= "Z":
            classes[1] = True
        elif "0" <= ch <= "9":
            classes[2] = True
        else:
            classes[3] = True
    if sum(classes) < 3:
        out.append("CLASSES")
    low = password.lower()
    if len(username) >= 3 and username.lower() in low:
        out.append("USERNAME")
    if any(password[i] == password[i + 1] == password[i + 2] for i in range(len(password) - 2)):
        out.append("REPEAT")
    if any(isinstance(b, str) and b.lower() == low for b in blocklist):
        out.append("BLOCKLIST")
    return out
