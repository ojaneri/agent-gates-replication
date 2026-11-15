from datetime import date, datetime, timedelta


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if isinstance(start, datetime) or not isinstance(start, date):
        raise TypeError("start must be a datetime.date (not datetime.datetime)")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")

    holiday_set = set()
    for h in holidays:
        if isinstance(h, datetime) or not isinstance(h, date):
            raise TypeError("holidays must contain datetime.date values only")
        holiday_set.add(h)

    def is_business_day(d: date) -> bool:
        return d.weekday() < 5 and d not in holiday_set

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
