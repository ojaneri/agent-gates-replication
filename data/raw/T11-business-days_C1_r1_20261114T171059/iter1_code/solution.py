from datetime import date, datetime, timedelta


def _validate(start, n, holidays):
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date, not a datetime")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")
    hol = set()
    for h in holidays:
        if isinstance(h, datetime) or not isinstance(h, date):
            raise TypeError("holidays must contain datetime.date values only")
        hol.add(h)
    return hol


def _is_business_day(d, hol):
    return d.weekday() < 5 and d not in hol


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    hol = _validate(start, n, holidays)

    if n == 0:
        cur = start
        while not _is_business_day(cur, hol):
            cur += timedelta(days=1)
        return cur

    step = timedelta(days=1 if n > 0 else -1)
    remaining = abs(n)
    cur = start
    while remaining > 0:
        cur += step
        if _is_business_day(cur, hol):
            remaining -= 1
    return cur
