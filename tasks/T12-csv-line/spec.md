# Parsing one delimited line

Implement `parse_line(line, sep=",")` in `solution.py`. It splits one line of delimited text into a list of field strings.

## Inputs

- `line` and `sep` must be `str`; otherwise raise `TypeError`.
- `sep` must be exactly one character, and must not be `"` (double quote), `\r` or `\n`. Otherwise raise `ValueError`.

## Fields

- Fields are separated by `sep`. A line with `k` separators outside quotes has `k + 1` fields, so `""` gives `[""]`, `"a,"` gives `["a", ""]` and `","` gives `["", ""]`.
- Whitespace is part of the field and is never trimmed: `" a , b"` gives `[" a ", " b"]`.
- **Quoted field:** a field whose first character is `"`. It ends at the next `"` that is not doubled. Inside it, `""` stands for one `"`, and the separator, `\r` and `\n` are ordinary characters. The quotes themselves are not part of the value: `'"a,b",c'` gives `["a,b", "c"]` and `'"say ""hi"""'` gives `['say "hi"']`.

## Errors (`ValueError`)

- A quoted field with no closing quote.
- Any character other than `sep` right after the closing quote of a quoted field (for example `'"a"b'` or `'"a" ,b'`).
- A `"` inside a field that does not start with `"` (for example `'a"b'`).
- A `\r` or `\n` outside a quoted field.
