from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=1):
    return datetime(2026, 1, day, hour, minute)


# ---------- can_book: input validation ----------

def test_end_equal_to_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(9), dt(9))


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(9))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(9), dt(10), buffer_minutes=-1)


def test_zero_buffer_is_accepted():
    assert can_book([], dt(9), dt(10), buffer_minutes=0) is True


# ---------- can_book: calendar day ----------

def test_booking_crossing_midnight_is_rejected():
    start = datetime(2026, 1, 1, 17, 0)
    end = datetime(2026, 1, 2, 0, 30)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59)) is False


def test_booking_on_same_day_is_accepted():
    assert can_book([], dt(9), dt(10)) is True


# ---------- can_book: duration ----------

def test_exactly_four_hours_is_allowed():
    assert can_book([], dt(8), dt(12)) is True


def test_longer_than_four_hours_is_rejected():
    assert can_book([], dt(8), dt(12, 1)) is False


def test_four_hours_and_one_second_is_rejected():
    assert can_book([], dt(8), datetime(2026, 1, 1, 12, 0, 1)) is False


# ---------- can_book: opening hours ----------

def test_start_exactly_at_open_time_is_allowed():
    assert can_book([], dt(8), dt(9)) is True


def test_start_before_open_time_is_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_end_exactly_at_close_time_is_allowed():
    assert can_book([], dt(17), dt(18)) is True


def test_end_after_close_time_is_rejected():
    assert can_book([], dt(17, 30), dt(18, 1)) is False


def test_custom_opening_hours_are_respected():
    open_t, close_t = time(10, 0), time(12, 0)
    assert can_book([], dt(10), dt(11), open_time=open_t, close_time=close_t) is True
    assert can_book([], dt(9, 30), dt(11), open_time=open_t, close_time=close_t) is False
    assert can_book([], dt(11), dt(12, 30), open_time=open_t, close_time=close_t) is False


# ---------- can_book: conflicts, no buffer ----------

def test_empty_room_accepts_booking():
    assert can_book([], dt(10), dt(11)) is True


def test_overlapping_booking_is_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10, 30), dt(11, 30)) is False


def test_new_booking_fully_inside_existing_is_rejected():
    existing = [(dt(9), dt(12))]
    assert can_book(existing, dt(10), dt(11)) is False


def test_new_booking_fully_containing_existing_is_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(9), dt(12)) is False


def test_identical_booking_is_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10), dt(11)) is False


def test_back_to_back_after_existing_is_allowed():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11), dt(12)) is True


def test_back_to_back_before_existing_is_allowed():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(9), dt(10)) is True


def test_booking_ending_one_minute_after_existing_start_conflicts():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(9), dt(10, 1)) is False


def test_checks_all_existing_bookings():
    existing = [(dt(8), dt(9)), (dt(10), dt(11)), (dt(13), dt(14))]
    assert can_book(existing, dt(12), dt(13, 30)) is False
    assert can_book(existing, dt(11), dt(13)) is True


def test_bookings_on_other_days_do_not_conflict():
    existing = [(datetime(2026, 1, 2, 10), datetime(2026, 1, 2, 11))]
    assert can_book(existing, dt(10), dt(11)) is True


# ---------- can_book: buffer ----------

def test_buffer_requires_gap_after_existing():
    existing = [(dt(10), dt(11))]
    # 15 minutes after the end is fine with a 15 minute buffer.
    assert can_book(existing, dt(11, 15), dt(12), buffer_minutes=15) is True
    # 14 minutes after the end is not.
    assert can_book(existing, dt(11, 14), dt(12), buffer_minutes=15) is False


def test_buffer_requires_gap_before_existing():
    existing = [(dt(10), dt(11))]
    # Ending exactly 15 minutes before the existing start is fine.
    assert can_book(existing, dt(9), dt(9, 45), buffer_minutes=15) is True
    # Ending 14 minutes before the existing start is not.
    assert can_book(existing, dt(9), dt(9, 46), buffer_minutes=15) is False


def test_buffer_applies_to_overlap_as_well():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10, 30), dt(11, 30), buffer_minutes=5) is False


def test_buffer_with_no_bookings_still_allows_booking():
    assert can_book([], dt(10), dt(11), buffer_minutes=60) is True


def test_buffer_allows_booking_far_from_existing():
    existing = [(dt(8), dt(9))]
    assert can_book(existing, dt(12), dt(13), buffer_minutes=30) is True


# ---------- merge_intervals ----------

def test_merge_empty_list():
    assert merge_intervals([]) == []


def test_merge_single_interval():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_disjoint_intervals_sorted():
    result = merge_intervals([(dt(13), dt(14)), (dt(9), dt(10))])
    assert result == [(dt(9), dt(10)), (dt(13), dt(14))]


def test_merge_overlapping_intervals():
    result = merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))])
    assert result == [(dt(9), dt(12))]


def test_merge_touching_intervals():
    result = merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(11))]


def test_merge_contained_interval_keeps_outer_end():
    result = merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(12))]


def test_merge_unsorted_chain_of_overlaps():
    result = merge_intervals([(dt(12), dt(13)), (dt(9), dt(10)), (dt(10), dt(11)), (dt(11), dt(12))])
    assert result == [(dt(9), dt(13))]


def test_merge_mixed_groups():
    intervals = [(dt(14), dt(15)), (dt(8), dt(9)), (dt(9), dt(10)), (dt(13), dt(14, 30))]
    assert merge_intervals(intervals) == [(dt(8), dt(10)), (dt(13), dt(15))]


def test_merge_does_not_modify_input():
    intervals = [(dt(13), dt(14)), (dt(9), dt(10)), (dt(9, 30), dt(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_raises_on_zero_length_interval():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(9))])


def test_merge_raises_on_reversed_interval():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(10)), (dt(12), dt(11))])
