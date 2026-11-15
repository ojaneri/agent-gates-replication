from datetime import datetime, time, timedelta


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must be non-negative")

    # Must start and end on the same calendar day.
    if start.date() != end.date():
        return False

    # Must not last more than 4 hours (exactly 4 hours is allowed).
    if end - start > timedelta(hours=4):
        return False

    # Must lie within opening hours (boundaries inclusive).
    if start.time() < open_time or end.time() > close_time:
        return False

    # Must not conflict with existing bookings, respecting the buffer.
    buffer = timedelta(minutes=buffer_minutes)
    for ex_start, ex_end in existing:
        starts_after = start >= ex_end + buffer
        ends_before = end + buffer <= ex_start
        if not (starts_after or ends_before):
            return False

    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for s, e in intervals:
        if e <= s:
            raise ValueError("each interval must have end > start")

    merged: list[tuple[datetime, datetime]] = []
    for s, e in sorted(intervals, key=lambda iv: iv[0]):
        if merged and s <= merged[-1][1]:
            last_s, last_e = merged[-1]
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))
    return merged
