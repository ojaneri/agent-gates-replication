from datetime import datetime, time, timedelta

MAX_DURATION = timedelta(hours=4)


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("booking must end after it starts")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must not be negative")
    if start.date() != end.date():
        return False
    if end - start > MAX_DURATION:
        return False
    if start.time() < open_time or end.time() > close_time:
        return False
    buffer = timedelta(minutes=buffer_minutes)
    for existing_start, existing_end in existing:
        clear_after = start - existing_end >= buffer
        clear_before = existing_start - end >= buffer
        if not (clear_after or clear_before):
            return False
    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for start, end in intervals:
        if end <= start:
            raise ValueError("interval must end after it starts")
    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals, key=lambda interval: interval[0]):
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged
