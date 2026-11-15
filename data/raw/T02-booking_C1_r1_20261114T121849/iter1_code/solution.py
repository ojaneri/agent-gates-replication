from datetime import datetime, time, timedelta


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must be non-negative")
    if start.date() != end.date():
        return False
    if end - start > timedelta(hours=4):
        return False
    if start.time() < open_time or end.time() > close_time:
        return False
    buffer = timedelta(minutes=buffer_minutes)
    for ex_start, ex_end in existing:
        starts_after = start >= ex_end + buffer
        ends_before = end <= ex_start - buffer
        if not (starts_after or ends_before):
            return False
    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for start, end in intervals:
        if end <= start:
            raise ValueError("interval end must be after start")
    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if merged and start <= merged[-1][1]:
            prev_start, prev_end = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged
