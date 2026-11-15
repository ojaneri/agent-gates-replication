# Password policy check

Implement `check_password` in `solution.py`.

```python
check_password(password: str, username: str, blocklist: set[str]) -> list[str]
```

It returns the codes of the rules the password violates, **in this order**: `"LENGTH"`, `"CLASSES"`, `"USERNAME"`, `"REPEAT"`, `"BLOCKLIST"`. A valid password gives an empty list.

## Rules

1. If `password` or `username` is not a `str`, raise `TypeError`.
2. **LENGTH**: the password must have between 12 and 64 characters (`len`), both ends allowed.
3. **CLASSES**: the password must contain characters from at least 3 of these 4 classes: ASCII lowercase letters `a`-`z`; ASCII uppercase letters `A`-`Z`; ASCII digits `0`-`9`; any other character (spaces, punctuation, non-ASCII letters such as `é` all count as "other").
4. **USERNAME**: violated if the username has 3 or more characters and appears inside the password, comparing both after `str.lower()`. A username shorter than 3 characters never triggers this rule.
5. **REPEAT**: violated if the same character appears 3 or more times in a row. The comparison is case-sensitive: `"aAa"` is not a repeat.
6. **BLOCKLIST**: violated if the password, after `str.lower()`, is equal to any blocklist entry after `str.lower()`. Containing a blocklisted word is not a violation; only equality is.
