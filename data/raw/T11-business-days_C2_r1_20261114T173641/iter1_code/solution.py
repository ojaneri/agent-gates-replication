from datetime import date, datetime, timedelta


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")

    holiday_set = set()
    for h in holidays:
        if not isinstance(h, date) or isinstance(h, datetime):
            raise TypeError("holidays must contain datetime.date values")
        holiday_set.add(h)

    def is_business_day(d: date) -> bool:
        return d.weekday() < 5 and d not in holiday_set

    if n == 0:
        current = start
        while not is_business_day(current):
            current += timedelta(days=1)
        return current

    step = timedelta(days=1 if n > 0 else -1)
    remaining = abs(n)
    current = start
    while remaining:
        current += step
        if is_business_day(current):
            remaining -= 1
    return current
