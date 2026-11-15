# Run-length encoding with an escape character

Implement `encode` and `decode` in `solution.py`. Both work on `str` (any Unicode characters).

## Encoded format

- A **maximal run** of the same character `c` repeated `n` times with `n >= 4` is written as `~` + `n` in decimal + `~` + `c`. For example `"aaaaa"` becomes `"~5~a"`, and a run of five `~` becomes `"~5~~"`.
- Every other character is written as itself, except `~`, which is written as `~~`. For example `"aaa"` stays `"aaa"`, and `"a~b"` becomes `"a~~b"`.
- Runs are maximal: `"aaaaaaaaaaaa"` (12 `a`) becomes `"~12~a"`, never two shorter runs.

## `encode(s: str) -> str`

Returns the encoded form of `s` as defined above. `encode("")` is `""`.

## `decode(t: str) -> str`

Reverses the encoding. It reads `t` left to right:

- A character other than `~` stands for itself.
- `~~` stands for one `~`.
- `~` followed by a decimal count, then `~`, then one character `c`, stands for `c` repeated count times. The count must have no leading zeros and must be at least 4.

Raise `ValueError` for anything else: a `~` at the end of the text, a `~` followed by something that is neither `~` nor a digit, a count with leading zeros, a count below 4, a count not followed by `~`, or a missing character after the second `~`.

`decode` also accepts well-formed text that `encode` would not produce, such as plain `"aaaa"` or two runs of the same character in a row.

For every string `s`, `decode(encode(s)) == s`.
