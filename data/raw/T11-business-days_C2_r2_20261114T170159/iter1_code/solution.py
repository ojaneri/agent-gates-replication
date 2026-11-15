from datetime import date, datetime, timedelta


def _check_start(start):
    if isinstance(start, datetime) or not isinstance(start, date):
        raise TypeError("start must be a datetime.date, not a datetime")


def _check_n(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")


def _collect_holidays(holidays):
    result = set()
    for h in holidays:
        if isinstance(h, datetime) or not isinstance(h, date):
            raise TypeError("holidays must contain datetime.date values only")
        result.add(h)
    return result


def _is_business_day(d, holidays):
    return d.weekday() < 5 and d not in holidays


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _check_start(start)
    _check_n(n)
    holiday_set = _collect_holidays(holidays)

    current = start
    if n == 0:
        while not _is_business_day(current, holiday_set):
            current += timedelta(days=1)
        return current

    step = timedelta(days=1) if n > 0 else timedelta(days=-1)
    remaining = abs(n)
    while remaining:
        current += step
        if _is_business_day(current, holiday_set):
            remaining -= 1
    return current
