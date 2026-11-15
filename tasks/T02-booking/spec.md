# Room booking

Implement two functions in `solution.py`. All datetimes are naive (no time zone).

## `can_book(existing, start, end, buffer_minutes=0, open_time=time(8, 0), close_time=time(18, 0)) -> bool`

Decides whether a new booking from `start` to `end` can be added to a room that already has the bookings in `existing` (a list of `(start, end)` datetime pairs).

Bookings are half-open intervals: a booking from 10:00 to 11:00 occupies the room from 10:00 up to, but not including, 11:00.

1. If `end <= start`, raise `ValueError`.
2. If `buffer_minutes` is negative, raise `ValueError`.
3. Return `False` if the booking does not start and end on the same calendar day.
4. Return `False` if the booking lasts more than 4 hours. Exactly 4 hours is allowed.
5. Return `False` if it starts before `open_time` or ends after `close_time`. Starting exactly at `open_time` or ending exactly at `close_time` is allowed.
6. Return `False` if it conflicts with any existing booking. With a buffer of `b` minutes, the new booking must either start at least `b` minutes after an existing booking ends, or end at least `b` minutes before it starts. With `b = 0`, back-to-back bookings (one ends at 11:00, the next starts at 11:00) are allowed.
7. Otherwise return `True`.

## `merge_intervals(intervals) -> list`

Takes a list of `(start, end)` datetime pairs in any order and returns a new list, sorted by start, in which overlapping or touching intervals are merged into one. Touching means one ends exactly when the other starts. Raise `ValueError` if any interval has `end <= start`. The input list must not be modified.
