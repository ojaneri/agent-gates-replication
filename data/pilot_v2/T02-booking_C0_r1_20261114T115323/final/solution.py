from datetime import datetime, time, timedelta


MAX_DURATION = timedelta(hours=4)


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must be non-negative")

    if start.date() != end.date():
        return False
    if end - start > MAX_DURATION:
        return False
    if start.time() < open_time or end.time() > close_time:
        return False

    buffer = timedelta(minutes=buffer_minutes)
    for ex_start, ex_end in existing:
        # Allowed if the new booking starts at least `buffer` after the existing one ends,
        # or ends at least `buffer` before the existing one starts.
        ok = start >= ex_end + buffer or end <= ex_start - buffer
        if not ok:
            return False

    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for s, e in intervals:
        if e <= s:
            raise ValueError("interval end must be after start")

    result: list[tuple[datetime, datetime]] = []
    for s, e in sorted(intervals, key=lambda iv: iv[0]):
        if result and s <= result[-1][1]:
            prev_s, prev_e = result[-1]
            result[-1] = (prev_s, max(prev_e, e))
        else:
            result.append((s, e))
    return result
