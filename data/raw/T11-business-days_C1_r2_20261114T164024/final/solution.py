from datetime import date, datetime, timedelta


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a date")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    hol = set()
    for h in holidays:
        if not isinstance(h, date) or isinstance(h, datetime):
            raise TypeError("holidays must be dates")
        hol.add(h)

    def is_bd(d):
        return d.weekday() < 5 and d not in hol

    cur = start
    if n == 0:
        while not is_bd(cur):
            cur += timedelta(days=1)
        return cur
    step = timedelta(days=1 if n > 0 else -1)
    remaining = abs(n)
    while remaining:
        cur += step
        if is_bd(cur):
            remaining -= 1
    return cur
