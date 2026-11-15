from datetime import date, datetime, timedelta


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")

    hol = set()
    for h in holidays:
        if not isinstance(h, date) or isinstance(h, datetime):
            raise TypeError("holidays must contain datetime.date values only")
        hol.add(h)

    def is_business_day(d: date) -> bool:
        return d.weekday() < 5 and d not in hol

    if n == 0:
        d = start
        while not is_business_day(d):
            d += timedelta(days=1)
        return d

    step = timedelta(days=1) if n > 0 else timedelta(days=-1)
    remaining = abs(n)
    d = start
    while remaining:
        d += step
        if is_business_day(d):
            remaining -= 1
    return d
