from datetime import date, datetime, timedelta


def _is_date(value) -> bool:
    return isinstance(value, date) and not isinstance(value, datetime)


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not _is_date(start):
        raise TypeError("start must be a date")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")
    hol = set()
    for h in holidays:
        if not _is_date(h):
            raise TypeError("holidays must be dates")
        hol.add(h)

    def is_biz(d):
        return d.weekday() < 5 and d not in hol

    step = timedelta(days=-1 if n < 0 else 1)
    current = start
    if n == 0:
        while not is_biz(current):
            current += step
        return current
    remaining = abs(n)
    while remaining:
        current += step
        if is_biz(current):
            remaining -= 1
    return current
