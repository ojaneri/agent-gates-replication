def check_password(password: str, username: str, blocklist: set[str]) -> list[str]:
    """Return the violated rule codes in order. See spec.md."""
    if not isinstance(password, str) or not isinstance(username, str):
        raise TypeError("password and username must be str")

    result = []

    if not (12 <= len(password) <= 64):
        result.append("LENGTH")

    classes = set()
    for ch in password:
        if "a" <= ch <= "z":
            classes.add(0)
        elif "A" <= ch <= "Z":
            classes.add(1)
        elif "0" <= ch <= "9":
            classes.add(2)
        else:
            classes.add(3)
    if len(classes) < 3:
        result.append("CLASSES")

    if len(username) >= 3 and username.lower() in password.lower():
        result.append("USERNAME")

    for i in range(len(password) - 2):
        if password[i] == password[i + 1] == password[i + 2]:
            result.append("REPEAT")
            break

    lowered = password.lower()
    if any(isinstance(b, str) and b.lower() == lowered for b in (blocklist or ())):
        result.append("BLOCKLIST")

    return result
