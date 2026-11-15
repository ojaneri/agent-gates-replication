from datetime import date, datetime, timedelta


def _check_start(start):
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date")


def _check_n(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")


def _check_holiday(h):
    if not isinstance(h, date) or isinstance(h, datetime):
        raise TypeError("holidays must contain datetime.date values")


def _holiday_set(holidays):
    result = set()
    for h in holidays:
        _check_holiday(h)
        result.add(h)
    return result


def _is_business_day(d, holiday_set):
    return d.weekday() < 5 and d not in holiday_set


def _next_business_day(start, holiday_set):
    current = start
    while not _is_business_day(current, holiday_set):
        current += timedelta(days=1)
    return current


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _check_start(start)
    _check_n(n)
    holiday_set = _holiday_set(holidays)

    if n == 0:
        return _next_business_day(start, holiday_set)

    step = timedelta(days=1 if n > 0 else -1)
    remaining = abs(n)
    current = start
    while remaining:
        current += step
        if _is_business_day(current, holiday_set):
            remaining -= 1
    return current
