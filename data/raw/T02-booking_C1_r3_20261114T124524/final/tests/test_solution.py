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


def test_rules():
    assert can_book([], d(10), d(11))
    assert not can_book([], d(10), d(10, 0, 2))
    assert can_book([], d(8), d(12))
    assert not can_book([], d(8), d(12, 1))
    assert can_book([], d(8), d(9))
    assert not can_book([], d(7, 59), d(9))
    assert can_book([], d(17), d(18))
    assert not can_book([], d(17), d(18, 1))
    assert can_book([], d(9), d(10), open_time=time(9), close_time=time(10))


def test_conflicts():
    ex = [(d(10), d(11))]
    assert can_book(ex, d(11), d(12))
    assert can_book(ex, d(9), d(10))
    assert not can_book(ex, d(10, 30), d(12))
    assert not can_book(ex, d(9), d(10, 30))
    assert not can_book(ex, d(10), d(11))
    assert not can_book(ex, d(11), d(12), buffer_minutes=15)
    assert can_book(ex, d(11, 15), d(12), buffer_minutes=15)
    assert not can_book(ex, d(8), d(10), buffer_minutes=15)
    assert can_book(ex, d(8), d(9, 45), buffer_minutes=15)


def test_merge():
    inp = [(d(12), d(13)), (d(9), d(10)), (d(10), d(11)), (d(9, 30), d(10, 30)), (d(12, 10), d(12, 20))]
    copy = list(inp)
    assert merge_intervals(inp) == [(d(9), d(11)), (d(12), d(13))]
    assert inp == copy
    assert merge_intervals([]) == []
    assert merge_intervals([(d(9), d(10)), (d(11), d(12))]) == [(d(9), d(10)), (d(11), d(12))]
    with pytest.raises(ValueError):
        merge_intervals([(d(10), d(10))])
