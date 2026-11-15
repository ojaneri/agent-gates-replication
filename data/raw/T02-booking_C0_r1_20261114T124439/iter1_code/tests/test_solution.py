from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=1):
    return datetime(2024, 1, day, h, m)


def test_invalid():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))
    with pytest.raises(ValueError):
        can_book([], d(10), d(9))
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_multi_day_and_duration():
    assert not can_book([], d(10), d(9, day=2))
    assert can_book([], d(9), d(13))
    assert not can_book([], d(9), d(13, 1))


def test_hours():
    assert can_book([], d(8), d(9))
    assert can_book([], d(17), d(18))
    assert not can_book([], d(7, 59), d(9))
    assert not can_book([], d(17), d(18, 1))
    assert can_book([], d(6), d(7), open_time=time(6), close_time=time(7))


def test_conflicts():
    ex = [(d(10), d(11))]
    assert can_book(ex, d(11), d(12))
    assert can_book(ex, d(9), d(10))
    assert not can_book(ex, d(10, 30), d(11, 30))
    assert not can_book(ex, d(9, 30), d(10, 30))
    assert not can_book(ex, d(9), d(12))
    assert not can_book(ex, d(10), d(11))


def test_buffer():
    ex = [(d(10), d(11))]
    assert not can_book(ex, d(11), d(12), buffer_minutes=15)
    assert can_book(ex, d(11, 15), d(12), buffer_minutes=15)
    assert can_book(ex, d(9), d(9, 45), buffer_minutes=15)
    assert not can_book(ex, d(9), d(9, 46), buffer_minutes=15)


def test_merge():
    src = [(d(12), d(13)), (d(8), d(9)), (d(9), d(10)), (d(12, 30), d(12, 45)), (d(15), d(16))]
    copy = list(src)
    assert merge_intervals(src) == [(d(8), d(10)), (d(12), d(13)), (d(15), d(16))]
    assert src == copy
    assert merge_intervals([]) == []
    with pytest.raises(ValueError):
        merge_intervals([(d(9), d(9))])
