from datetime import datetime, time, timedelta


def _conflicts(existing, start, end, buf):
    for s, e in existing:
        if not (start >= e + buf or end + buf <= s):
            return True
    return False


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer must be non-negative")
    if start.date() != end.date():
        return False
    if end - start > timedelta(hours=4):
        return False
    if start.time() < open_time or end.time() > close_time:
        return False
    return not _conflicts(existing, start, end, timedelta(minutes=buffer_minutes))


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for s, e in intervals:
        if e <= s:
            raise ValueError("end must be after start")
    merged = []
    for s, e in sorted(intervals):
        if merged and s <= merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged
