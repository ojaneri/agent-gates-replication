from datetime import datetime, time, timedelta

MAX_DURATION = timedelta(hours=4)


def _check_booking(start: datetime, end: datetime, buffer_minutes: int) -> None:
    """Raise ValueError for invalid booking arguments."""
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer_minutes must not be negative")


def _fits_window(start: datetime, end: datetime, open_time: time, close_time: time) -> bool:
    """Return True if the booking is on one day, at most 4 hours, and within opening hours."""
    if start.date() != end.date():
        return False
    if end - start > MAX_DURATION:
        return False
    return start.time() >= open_time and end.time() <= close_time


def _conflicts(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime,
               buffer_minutes: int) -> bool:
    """Return True if the booking conflicts with any existing booking, including the buffer."""
    gap = timedelta(minutes=buffer_minutes)
    for booked_start, booked_end in existing:
        if start < booked_end + gap and end > booked_start - gap:
            return True
    return False


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    _check_booking(start, end, buffer_minutes)
    if not _fits_window(start, end, open_time, close_time):
        return False
    return not _conflicts(existing, start, end, buffer_minutes)


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    for start, end in intervals:
        if end <= start:
            raise ValueError("interval end must be after start")
    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            prev_start, prev_end = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged
