from datetime import date, datetime, timedelta


def _check_date(value, name):
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.date, not {type(value).__name__}")


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _check_date(start, "start")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")

    holiday_set = set()
    for holiday in holidays:
        _check_date(holiday, "holiday")
        holiday_set.add(holiday)

    def is_business_day(day):
        return day.weekday() < 5 and day not in holiday_set

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
