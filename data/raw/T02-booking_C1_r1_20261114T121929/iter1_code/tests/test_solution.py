from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=1):
    return datetime(2024, 1, day, h, m)


def test_invalid():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_day_duration_hours():
    assert not can_book([], d(10), d(9, day=2))
    assert not can_book([], datetime(2024, 1, 1, 17), datetime(2024, 1, 2, 1))
    assert can_book([], d(9), d(13))
    assert not can_book([], d(9), d(13, 1))
    assert can_book([], d(8), d(10))
    assert not can_book([], d(7, 59), d(10))
    assert can_book([], d(16), d(18))
    assert not can_book([], d(16), d(18, 1))
    assert can_book([], d(6), d(7), open_time=time(6), close_time=time(7))


def test_conflicts():
    ex = [(d(10), d(11))]
    assert not can_book(ex, d(10, 30), d(11, 30))
    assert not can_book(ex, d(9, 30), d(10, 30))
    assert not can_book(ex, d(9), d(12))
    assert can_book(ex, d(11), d(12))
    assert can_book(ex, d(9), d(10))
    assert not can_book(ex, d(11), d(12), buffer_minutes=15)
    assert can_book(ex, d(11, 15), d(12), buffer_minutes=15)
    assert not can_book(ex, d(9), d(10), buffer_minutes=15)
    assert can_book(ex, d(9), d(9, 45), buffer_minutes=15)


def test_merge():
    inp = [(d(12), d(13)), (d(9), d(10)), (d(10), d(11)), (d(9, 30), d(9, 45)), (d(12, 30), d(14))]
    copy = list(inp)
    assert merge_intervals(inp) == [(d(9), d(11)), (d(12), d(14))]
    assert inp == copy
    assert merge_intervals([]) == []
    with pytest.raises(ValueError):
        merge_intervals([(d(10), d(10))])
