from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=1):
    return datetime(2024, 1, day, h, m)


def test_invalid_args():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))
    with pytest.raises(ValueError):
        can_book([], d(10), d(9))
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_day_duration_hours():
    assert not can_book([], d(10), d(9, 0, 2))
    assert not can_book([], d(8), d(12, 1))
    assert can_book([], d(8), d(12))
    assert not can_book([], d(7, 59), d(9))
    assert can_book([], d(16), d(18))
    assert not can_book([], d(16), d(18, 1))
    assert can_book([], d(6), d(7), open_time=time(6), close_time=time(7))


def test_conflicts():
    ex = [(d(10), d(11))]
    assert not can_book(ex, d(10, 30), d(11, 30))
    assert not can_book(ex, d(9), d(10, 30))
    assert not can_book(ex, d(10), d(11))
    assert can_book(ex, d(11), d(12))
    assert can_book(ex, d(9), d(10))
    assert not can_book(ex, d(11), d(12), buffer_minutes=10)
    assert can_book(ex, d(11, 10), d(12), buffer_minutes=10)
    assert not can_book(ex, d(9), d(10), buffer_minutes=10)
    assert can_book(ex, d(8), d(9, 50), buffer_minutes=10)


def test_merge():
    src = [(d(12), d(13)), (d(8), d(10)), (d(10), d(11)), (d(9), d(9, 30)), (d(14), d(15))]
    copy = list(src)
    assert merge_intervals(src) == [(d(8), d(11)), (d(12), d(13)), (d(14), d(15))]
    assert src == copy
    assert merge_intervals([]) == []
    with pytest.raises(ValueError):
        merge_intervals([(d(10), d(10))])
