from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def at(h, m=0, day=16):
    return datetime(2026, 11, day, h, m)


EXISTING = [(at(10), at(11)), (at(14), at(15))]


# can_book: validation
def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], at(11), at(10))


def test_zero_length_raises():
    with pytest.raises(ValueError):
        can_book([], at(11), at(11))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], at(9), at(10), buffer_minutes=-1)


# can_book: free room and limits
def test_free_room():
    assert can_book([], at(9), at(10)) is True


def test_exactly_four_hours_allowed():
    assert can_book([], at(9), at(13)) is True


def test_more_than_four_hours_rejected():
    assert can_book([], at(9), at(13, 1)) is False


def test_start_at_opening_allowed():
    assert can_book([], at(8), at(9)) is True


def test_start_before_opening_rejected():
    assert can_book([], at(7, 59), at(9)) is False


def test_end_at_closing_allowed():
    assert can_book([], at(17), at(18)) is True


def test_end_after_closing_rejected():
    assert can_book([], at(17), at(18, 1)) is False


def test_custom_hours():
    assert can_book([], at(6), at(7), open_time=time(6), close_time=time(22)) is True
    assert can_book([], at(21), at(22, 30), open_time=time(6), close_time=time(22)) is False


def test_multi_day_rejected():
    # 3 hours long, inside opening hours by clock time, but crosses midnight
    assert can_book([], datetime(2026, 11, 16, 22), datetime(2026, 11, 17, 1),
                    open_time=time(0), close_time=time(23, 59)) is False


# can_book: conflicts
def test_overlap_rejected():
    assert can_book(EXISTING, at(10, 30), at(11, 30)) is False


def test_contained_rejected():
    assert can_book(EXISTING, at(10, 15), at(10, 45)) is False


def test_containing_rejected():
    assert can_book(EXISTING, at(9), at(12)) is False


def test_back_to_back_after_allowed():
    assert can_book(EXISTING, at(11), at(12)) is True


def test_back_to_back_before_allowed():
    assert can_book(EXISTING, at(9), at(10)) is True


def test_buffer_after_existing():
    assert can_book(EXISTING, at(11), at(12), buffer_minutes=15) is False
    assert can_book(EXISTING, at(11, 15), at(12), buffer_minutes=15) is True


def test_buffer_before_existing():
    assert can_book(EXISTING, at(9), at(10), buffer_minutes=15) is False
    assert can_book(EXISTING, at(9), at(9, 45), buffer_minutes=15) is True


def test_between_two_bookings_with_buffer():
    assert can_book(EXISTING, at(11, 30), at(13, 30), buffer_minutes=30) is True
    assert can_book(EXISTING, at(11, 30), at(13, 31), buffer_minutes=30) is False


def test_other_day_bookings_do_not_conflict():
    other = [(at(10, day=17), at(11, day=17))]
    assert can_book(other, at(10), at(11)) is True


# merge_intervals
def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_sorts_input():
    assert merge_intervals([(at(14), at(15)), (at(9), at(10))]) == [(at(9), at(10)), (at(14), at(15))]


def test_merge_overlapping():
    assert merge_intervals([(at(9), at(11)), (at(10), at(12))]) == [(at(9), at(12))]


def test_merge_touching():
    assert merge_intervals([(at(9), at(10)), (at(10), at(11))]) == [(at(9), at(11))]


def test_merge_contained_keeps_outer_end():
    assert merge_intervals([(at(9), at(13)), (at(10), at(11))]) == [(at(9), at(13))]


def test_merge_chain_unsorted():
    got = merge_intervals([(at(12), at(13)), (at(9), at(10)), (at(10), at(12)), (at(15), at(16))])
    assert got == [(at(9), at(13)), (at(15), at(16))]


def test_merge_invalid_interval():
    with pytest.raises(ValueError):
        merge_intervals([(at(9), at(9))])


def test_merge_does_not_modify_input():
    data = [(at(14), at(15)), (at(9), at(10))]
    copy = list(data)
    merge_intervals(data)
    assert data == copy
