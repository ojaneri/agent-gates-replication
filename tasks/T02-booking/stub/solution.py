from datetime import datetime, time


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    """Return True if the booking can be added. See spec.md."""
    raise NotImplementedError


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Return sorted, merged intervals. See spec.md."""
    raise NotImplementedError
