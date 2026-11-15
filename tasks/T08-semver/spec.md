# Version comparison

Implement `compare_versions` in `solution.py`.

```python
compare_versions(a: str, b: str) -> int
```

Returns `-1` if `a` has lower precedence than `b`, `0` if equal precedence, `1` if higher.

## Version format

`MAJOR.MINOR.PATCH`, optionally followed by `-PRERELEASE`, optionally followed by `+BUILD`.

- `MAJOR`, `MINOR` and `PATCH` are non-negative integers written in decimal without leading zeros (`0` is fine, `01` is not).
- `PRERELEASE` is one or more identifiers separated by dots. Each identifier is non-empty and uses only ASCII letters, digits and `-`. An identifier made only of digits is *numeric* and must not have leading zeros (`0` is fine, `07` is not).
- `BUILD` is one or more non-empty identifiers separated by dots, using only ASCII letters, digits and `-`. Leading zeros are allowed in build identifiers.
- Anything else (missing parts, extra parts, spaces, empty identifiers) is invalid: raise `ValueError`.

## Precedence

1. Compare `MAJOR`, then `MINOR`, then `PATCH`, numerically.
2. If they are equal, a version **without** a prerelease has higher precedence than one with a prerelease (`1.0.0-alpha < 1.0.0`).
3. If both have a prerelease, compare identifiers left to right:
   - two numeric identifiers compare numerically;
   - two non-numeric identifiers compare as ASCII strings;
   - a numeric identifier has lower precedence than a non-numeric one;
   - if all compared identifiers are equal, the version with fewer identifiers has lower precedence.
4. `BUILD` is ignored for precedence: `1.0.0+a` and `1.0.0+b` are equal.
