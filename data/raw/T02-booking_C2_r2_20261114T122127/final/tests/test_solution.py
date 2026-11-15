from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=1):
    return datetime(2024, 1, day, h, m)


EX = [(d(10), d(11))]


def test_invalid():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))
    with pytest.raises(ValueError):
        can_book([], d(11), d(10))
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_day_and_duration():
    assert not can_book([], d(10), d(9, 0, 2))
    assert not can_book([], d(8), d(12, 1))
    assert can_book([], d(8), d(12))
    assert can_book([], d(14), d(18))


def test_hours():
    assert not can_book([], d(7, 59), d(9))
    assert not can_book([], d(17), d(18, 1))
    assert can_book([], d(8), d(9))
    assert can_book([], d(17), d(18))
    assert not can_book([], d(9), d(10), open_time=time(9, 30))
    assert can_book([], d(9, 30), d(10), open_time=time(9, 30))
    assert not can_book([], d(9), d(10), close_time=time(9, 30))
    assert can_book([], d(9), d(9, 30), close_time=time(9, 30))


def test_conflicts():
    assert not can_book(EX, d(10), d(11))
    assert not can_book(EX, d(9), d(10, 30))
    assert not can_book(EX, d(10, 30), d(12))
    assert not can_book(EX, d(10, 15), d(10, 45))
    assert not can_book(EX, d(9), d(12))
    assert can_book(EX, d(11), d(12))
    assert can_book(EX, d(9), d(10))
    assert can_book(EX, d(12), d(13))


def test_buffer():
    assert not can_book(EX, d(11), d(12), 15)
    assert not can_book(EX, d(11, 14), d(12), 15)
    assert can_book(EX, d(11, 15), d(12), 15)
    assert not can_book(EX, d(9), d(10), 15)
    assert not can_book(EX, d(9), d(9, 46), 15)
    assert can_book(EX, d(9), d(9, 45), 15)


def test_merge():
    a, b, c = (d(9), d(10)), (d(10), d(11)), (d(12), d(13))
    inp = [c, b, a]
    assert merge_intervals(inp) == [(d(9), d(11)), c]
    assert inp == [c, b, a]
    assert merge_intervals([]) == []
    assert merge_intervals([(d(9), d(12)), (d(10), d(11))]) == [(d(9), d(12))]
    assert merge_intervals([(d(9), d(11)), (d(10), d(12))]) == [(d(9), d(12))]
    assert merge_intervals([(d(9), d(10)), (d(11), d(12))]) == [(d(9), d(10)), (d(11), d(12))]
    with pytest.raises(ValueError):
        merge_intervals([(d(9), d(9))])
    with pytest.raises(ValueError):
        merge_intervals([(d(10), d(9))])
