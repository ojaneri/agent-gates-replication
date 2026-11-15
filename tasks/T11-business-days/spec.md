# Adding business days

Implement `add_business_days(start, n, holidays=())` in `solution.py`. It returns a `datetime.date`.

## Definitions

A **business day** is a Monday to Friday that is not in `holidays`.

## Behaviour

- `n > 0`: move forward from `start` and return the date of the `n`-th business day **after** `start`. `start` itself is never counted, whether or not it is a business day.
- `n < 0`: the same, moving backward: return the `|n|`-th business day **before** `start`.
- `n == 0`: return `start` if it is a business day; otherwise return the **next** business day after it.

## Inputs

- `start` must be a `datetime.date` and not a `datetime.datetime`; otherwise raise `TypeError`.
- `n` must be an `int`; `bool` and `float` raise `TypeError`.
- `holidays` is any iterable of `datetime.date` values (list, set, tuple, generator). An element that is not a `date`, or that is a `datetime`, raises `TypeError`. Holidays that fall on a weekend change nothing.
