from datetime import datetime, time, timedelta

MAX_DURATION = timedelta(hours=4)


def _conflicts(existing_start: datetime, existing_end: datetime,
               start: datetime, end: datetime, buffer: timedelta) -> bool:
    """Return True if [start, end) is too close to [existing_start, existing_end) given the buffer."""
    starts_too_soon = start < existing_end + buffer
    ends_too_late = existing_start < end + buffer
    return starts_too_soon and ends_too_late


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
    for existing_start, existing_end in existing:
        if _conflicts(existing_start, existing_end, start, end, buffer):
            return False
    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for start, end in intervals:
        if end <= start:
            raise ValueError("each interval must have end after start")
    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
