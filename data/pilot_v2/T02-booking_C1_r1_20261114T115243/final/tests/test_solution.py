from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=14):
    return datetime(2026, 11, day, hour, minute)


# ---- can_book ----

def test_empty_room_accepts_booking_in_hours():
    assert can_book([], dt(9), dt(10)) is True


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(9))


def test_end_equal_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(9), dt(10), buffer_minutes=-1)


def test_zero_buffer_is_allowed():
    assert can_book([], dt(9), dt(10), buffer_minutes=0) is True


def test_different_days_rejected():
    assert can_book([], datetime(2026, 11, 14, 17), datetime(2026, 11, 15, 9)) is False


def test_exactly_four_hours_allowed():
    assert can_book([], dt(8), dt(12)) is True


def test_longer_than_four_hours_rejected():
    assert can_book([], dt(8), dt(12, 1)) is False


def test_start_before_open_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_start_exactly_at_open_allowed():
    assert can_book([], dt(8), dt(9)) is True


def test_end_after_close_rejected():
    assert can_book([], dt(17), dt(18, 1)) is False


def test_end_exactly_at_close_allowed():
    assert can_book([], dt(17), dt(18)) is True


def test_custom_open_and_close_times():
    assert can_book([], dt(7), dt(8), open_time=time(7), close_time=time(9)) is True
    assert can_book([], dt(6), dt(7), open_time=time(7), close_time=time(9)) is False
    assert can_book([], dt(8), dt(10), open_time=time(7), close_time=time(9)) is False


def test_overlap_with_existing_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10, 30), dt(11, 30)) is False


def test_new_booking_contained_in_existing_rejected():
    existing = [(dt(9), dt(12))]
    assert can_book(existing, dt(10), dt(11)) is False


def test_existing_contained_in_new_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(9), dt(12)) is False


def test_back_to_back_allowed_with_zero_buffer():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11), dt(12)) is True
    assert can_book(existing, dt(9), dt(10)) is True


def test_back_to_back_rejected_with_buffer():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11), dt(12), buffer_minutes=15) is False
    assert can_book(existing, dt(9), dt(10), buffer_minutes=15) is False


def test_buffer_exactly_satisfied_allowed():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11, 15), dt(12), buffer_minutes=15) is True
    assert can_book(existing, dt(8, 30), dt(9, 45), buffer_minutes=15) is True


def test_buffer_one_minute_short_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11, 14), dt(12), buffer_minutes=15) is False
    assert can_book(existing, dt(8, 30), dt(9, 46), buffer_minutes=15) is False


def test_no_conflict_with_far_bookings():
    existing = [(dt(9), dt(9, 30)), (dt(14), dt(15))]
    assert can_book(existing, dt(10), dt(11), buffer_minutes=30) is True


# ---- merge_intervals ----

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_sorts_disjoint_intervals():
    assert merge_intervals([(dt(12), dt(13)), (dt(9), dt(10))]) == [
        (dt(9), dt(10)),
        (dt(12), dt(13)),
    ]


def test_merge_overlapping():
    assert merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))]) == [(dt(9), dt(12))]


def test_merge_touching():
    assert merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))]) == [(dt(9), dt(11))]


def test_merge_contained_keeps_outer_end():
    assert merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))]) == [(dt(9), dt(12))]


def test_merge_chain_in_unsorted_order():
    intervals = [(dt(13), dt(14)), (dt(9), dt(10)), (dt(10), dt(11)), (dt(11), dt(12)), (dt(15), dt(16))]
    assert merge_intervals(intervals) == [(dt(9), dt(12)), (dt(13), dt(14)), (dt(15), dt(16))]


def test_merge_does_not_modify_input():
    intervals = [(dt(12), dt(13)), (dt(9), dt(10))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(9))])
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(9))])
