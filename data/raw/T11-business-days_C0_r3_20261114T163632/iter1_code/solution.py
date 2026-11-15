from datetime import date, datetime, timedelta


def _validate_date(value, name):
    if isinstance(value, datetime) or not isinstance(value, date):
        raise TypeError(f"{name} must be a datetime.date, not {type(value).__name__}")


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _validate_date(start, "start")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, not {type(n).__name__}")

    holiday_set = set()
    for h in holidays:
        _validate_date(h, "holiday")
        holiday_set.add(h)

    def is_business_day(d: date) -> bool:
        return d.weekday() < 5 and d not in holiday_set

    if n == 0:
        current = start
        while not is_business_day(current):
            current += timedelta(days=1)
        return current

    step = timedelta(days=1) if n > 0 else timedelta(days=-1)
    remaining = abs(n)
    current = start
    while remaining:
        current += step
        if is_business_day(current):
            remaining -= 1
    return current
