from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=1):
    return datetime(2024, 1, day, h, m)


EX = [(d(10), d(11))]


def test_errors():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))
    with pytest.raises(ValueError):
        can_book([], d(11), d(10))
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_basic_and_limits():
    assert can_book([], d(10), d(11))
    assert not can_book([], d(22), datetime(2024, 1, 2, 1))
    assert can_book([], d(9), d(13))
    assert not can_book([], d(9), d(13, 1))
    assert can_book([], d(8), d(10))
    assert not can_book([], d(7, 59), d(10))
    assert can_book([], d(16), d(18))
    assert not can_book([], d(16), d(18, 1))
    assert can_book([], d(9), d(10), open_time=time(9), close_time=time(10))
    assert not can_book([], d(9), d(10), open_time=time(9, 30))


def test_conflicts():
    assert not can_book(EX, d(10, 30), d(11, 30))
    assert not can_book(EX, d(9, 30), d(10, 30))
    assert not can_book(EX, d(10), d(11))
    assert not can_book(EX, d(9), d(12))
    assert can_book(EX, d(11), d(12))
    assert can_book(EX, d(9), d(10))
    assert can_book(EX, d(9), d(10), day_buf := 0)


def test_buffer():
    assert not can_book(EX, d(11, 29), d(12), buffer_minutes=30)
    assert can_book(EX, d(11, 30), d(12), buffer_minutes=30)
    assert not can_book(EX, d(9), d(9, 31), buffer_minutes=30)
    assert can_book(EX, d(9), d(9, 30), buffer_minutes=30)
    assert not can_book(EX, d(11), d(12), buffer_minutes=1)


def test_merge():
    src = [(d(12), d(13)), (d(9), d(10)), (d(9, 30), d(11)), (d(11), d(11, 30)), (d(9, 15), d(9, 20))]
    copy = list(src)
    assert merge_intervals(src) == [(d(9), d(11, 30)), (d(12), d(13))]
    assert src == copy
    assert merge_intervals([]) == []
    assert merge_intervals([(d(9), d(10)), (d(10, 1), d(11))]) == [(d(9), d(10)), (d(10, 1), d(11))]
    with pytest.raises(ValueError):
        merge_intervals([(d(9), d(9))])
