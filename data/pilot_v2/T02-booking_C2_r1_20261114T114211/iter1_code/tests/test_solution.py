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


def test_basic_true():
    assert can_book([], d(10), d(11)) is True


def test_multi_day():
    assert can_book([], d(17), d(9, day=2)) is False


def test_duration():
    assert can_book([], d(9), d(13)) is True
    assert can_book([], d(9), d(13, 1)) is False


def test_hours():
    assert can_book([], d(8), d(9)) is True
    assert can_book([], d(7, 59), d(9)) is False
    assert can_book([], d(17), d(18)) is True
    assert can_book([], d(17), d(18, 1)) is False
    assert can_book([], d(9), d(10), open_time=time(9), close_time=time(10)) is True
    assert can_book([], d(8), d(10), open_time=time(9), close_time=time(10)) is False


def test_conflicts():
    assert can_book(EX, d(10), d(11)) is False
    assert can_book(EX, d(10, 30), d(12)) is False
    assert can_book(EX, d(9), d(10, 30)) is False
    assert can_book(EX, d(9), d(12)) is False
    assert can_book(EX, d(10, 15), d(10, 45)) is False
    assert can_book(EX, d(11), d(12)) is True
    assert can_book(EX, d(9), d(10)) is True
    assert can_book(EX, d(12), d(13)) is True


def test_buffer():
    assert can_book(EX, d(11), d(12), 15) is False
    assert can_book(EX, d(11, 15), d(12), 15) is True
    assert can_book(EX, d(11, 14), d(12), 15) is False
    assert can_book(EX, d(9), d(9, 45), 15) is True
    assert can_book(EX, d(9), d(9, 46), 15) is False


def test_merge():
    src = [(d(12), d(13)), (d(9), d(10)), (d(10), d(11)), (d(9, 30), d(10, 15)), (d(14), d(15)),
           (d(14, 10), d(14, 20))]
    copy = list(src)
    assert merge_intervals(src) == [(d(9), d(11)), (d(12), d(13)), (d(14), d(15))]
    assert src == copy
    assert merge_intervals([]) == []
    assert merge_intervals([(d(9), d(12)), (d(10), d(11))]) == [(d(9), d(12))]
    assert merge_intervals([(d(9), d(10)), (d(10, 1), d(11))]) == [(d(9), d(10)), (d(10, 1), d(11))]


def test_merge_invalid():
    with pytest.raises(ValueError):
        merge_intervals([(d(10), d(10))])
    with pytest.raises(ValueError):
        merge_intervals([(d(9), d(10)), (d(12), d(11))])
