from datetime import date, datetime, timedelta


def _is_business_day(d: date, holiday_set: set) -> bool:
    return d.weekday() < 5 and d not in holiday_set


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date, not datetime.datetime")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")

    holiday_set = set()
    for h in holidays:
        if not isinstance(h, date) or isinstance(h, datetime):
            raise TypeError("holidays must contain only datetime.date values")
        holiday_set.add(h)

    if n == 0:
        current = start
        while not _is_business_day(current, holiday_set):
            current += timedelta(days=1)
        return current

    step = timedelta(days=1) if n > 0 else timedelta(days=-1)
    remaining = abs(n)
    current = start
    while remaining > 0:
        current += step
        if _is_business_day(current, holiday_set):
            remaining -= 1
    return current
