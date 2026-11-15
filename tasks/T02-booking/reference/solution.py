from datetime import datetime, time, timedelta

MAX_DURATION = timedelta(hours=4)


def can_book(existing: list[tuple[datetime, datetime]], start: datetime, end: datetime, buffer_minutes: int = 0,
             open_time: time = time(8, 0), close_time: time = time(18, 0)) -> bool:
    if end <= start:
        raise ValueError("end must be after start")
    if buffer_minutes < 0:
        raise ValueError("buffer must be >= 0")
    if start.date() != end.date():
        return False
    if end - start > MAX_DURATION:
        return False
    if start.time() < open_time or end.time() > close_time:
        return False
    buf = timedelta(minutes=buffer_minutes)
    for ex_start, ex_end in existing:
        if start < ex_end + buf and ex_start < end + buf:
            return False
    return True


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    for s, e in intervals:
        if e <= s:
            raise ValueError("end must be after start")
    out: list[tuple[datetime, datetime]] = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out
