from datetime import datetime, time, timedelta


MAX_DURATION = timedelta(hours=4)


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("booking end must be after its start")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must not be negative")

    # Must start and end on the same calendar day.
    if start.date() != end.date():
        return False

    # At most 4 hours (exactly 4 hours is allowed).
    if end - start > MAX_DURATION:
        return False

    # Must fall within opening hours (edges are allowed).
    if start.time() < open_time or end.time() > close_time:
        return False

    # Half-open intervals with a buffer: the new booking must start at least
    # `buffer` after an existing one ends, or end at least `buffer` before it
    # starts. Otherwise it conflicts.
    buffer = timedelta(minutes=buffer_minutes)
    for booked_start, booked_end in existing:
        if start < booked_end + buffer and booked_start < end + buffer:
            return False

    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for interval_start, interval_end in intervals:
        if interval_end <= interval_start:
            raise ValueError("interval end must be after its start")

    merged: list[tuple[datetime, datetime]] = []
    for interval_start, interval_end in sorted(intervals, key=lambda pair: pair[0]):
        if merged and interval_start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, interval_end))
        else:
            merged.append((interval_start, interval_end))
    return merged
