# Safe archive extraction plan

Implement `plan_extraction` in `solution.py`. It decides where each member of an archive (for example a zip file) would be written, and refuses members that could write outside the destination ("zip slip"). It works only on strings: it must not touch the file system.

```python
plan_extraction(dest: str, members: list[str]) -> list[str]
```

`UnsafePathError` is already defined in the stub as a subclass of `ValueError`.

## Rules

1. `dest` must be a non-empty string, otherwise raise `ValueError`. Trailing `/` characters of `dest` are ignored, so `"out/"` behaves like `"out"`, and `"/"` means the root (members go to `"/name"`).
2. Member names use `/` as the separator. A backslash `\` is **also** a separator, because archives made on Windows use it.
3. Normalisation: empty segments (as in `a//b`) and `.` segments are dropped. A `..` segment removes the previous segment, so `a/../b` becomes `b`.
4. Raise `UnsafePathError` for a member that:
   - contains a NUL character;
   - is absolute: starts with `/` or `\`;
   - starts with a Windows drive prefix: a letter followed by `:` (as in `C:/x`, `c:x`, `C:\x`);
   - has a `..` that would climb above the destination at any point, even if later segments come back down (`a/../../b` is unsafe);
   - is empty after normalisation (as in `.`, `./` or `a/..`).
   A segment is `..` only if it is exactly two dots: names like `..a`, `a..` or `...` are ordinary names.
5. A member whose name ends with a separator is a directory entry. It is validated by the rules above, but it is not included in the result.
6. If two file members normalise to the same path, comparing case-insensitively (`A.txt` and `a.txt` are the same file on Windows and macOS), raise `UnsafePathError`: the second would overwrite the first.
7. Return the full target paths, `dest` + `/` + normalised member, for the file members in their input order. If any member is unsafe, raise; never return a partial plan.
