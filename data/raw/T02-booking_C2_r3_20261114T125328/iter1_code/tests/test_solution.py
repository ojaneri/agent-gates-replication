from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def at(hour, minute=0, day=4):
    """Datetime on 2024-03-<day> at the given time (day 4 by default)."""
    return datetime(2024, 3, day, hour, minute)


# ---------- can_book: argument validation ----------

def test_end_equal_to_start_raises():
    with pytest.raises(ValueError):
        can_book([], at(10), at(10))


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], at(11), at(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], at(10), at(11), buffer_minutes=-1)


def test_zero_buffer_is_accepted():
    assert can_book([], at(10), at(11), buffer_minutes=0) is True


# ---------- can_book: same-day rule ----------

def test_booking_across_midnight_is_rejected_even_inside_hours():
    start = at(23, 30, day=4)
    end = at(0, 30, day=5)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59, 59)) is False


def test_booking_across_midnight_is_rejected_with_default_hours():
    assert can_book([], at(17, 30, day=4), at(0, 30, day=5)) is False


# ---------- can_book: duration rule ----------

def test_exactly_four_hours_is_allowed():
    assert can_book([], at(9), at(13)) is True


def test_four_hours_and_one_minute_is_rejected():
    assert can_book([], at(9), at(13, 1)) is False


def test_longer_than_four_hours_is_rejected_with_long_opening_hours():
    assert can_book([], at(8), at(13, 1), open_time=time(0, 0), close_time=time(23, 59)) is False


def test_four_hours_is_allowed_with_long_opening_hours():
    assert can_book([], at(8), at(12), open_time=time(0, 0), close_time=time(23, 59)) is True


# ---------- can_book: opening hours ----------

def test_start_exactly_at_open_is_allowed():
    assert can_book([], at(8), at(9)) is True


def test_start_before_open_is_rejected():
    assert can_book([], at(7, 59), at(9)) is False


def test_end_exactly_at_close_is_allowed():
    assert can_book([], at(17), at(18)) is True


def test_end_after_close_is_rejected():
    assert can_book([], at(17), at(18, 1)) is False


def test_custom_opening_hours_are_respected():
    assert can_book([], at(9), at(10), open_time=time(9), close_time=time(12)) is True
    assert can_book([], at(8), at(10), open_time=time(9), close_time=time(12)) is False
    assert can_book([], at(11), at(13), open_time=time(9), close_time=time(12)) is False


# ---------- can_book: conflicts without buffer ----------

def test_empty_room_accepts_valid_booking():
    assert can_book([], at(10), at(11)) is True


def test_back_to_back_bookings_are_allowed_with_zero_buffer():
    existing = [(at(10), at(11))]
    assert can_book(existing, at(11), at(12)) is True
    assert can_book(existing, at(9), at(10)) is True


def test_overlap_at_start_of_existing_is_rejected():
    assert can_book([(at(10), at(11))], at(9, 30), at(10, 30)) is False


def test_overlap_at_end_of_existing_is_rejected():
    assert can_book([(at(10), at(11))], at(10, 30), at(11, 30)) is False


def test_booking_inside_existing_is_rejected():
    assert can_book([(at(9), at(12))], at(10), at(11)) is False


def test_booking_containing_existing_is_rejected():
    assert can_book([(at(10), at(11))], at(9), at(12)) is False


def test_identical_booking_is_rejected():
    assert can_book([(at(10), at(11))], at(10), at(11)) is False


def test_conflict_with_second_existing_booking_is_detected():
    existing = [(at(8), at(9)), (at(10), at(11))]
    assert can_book(existing, at(10, 30), at(11, 30)) is False


def test_non_conflicting_bookings_around_existing_are_accepted():
    existing = [(at(8), at(9)), (at(12), at(13))]
    assert can_book(existing, at(10), at(11)) is True


def test_empty_existing_list_with_buffer_is_accepted():
    assert can_book([], at(10), at(11), buffer_minutes=60) is True


# ---------- can_book: buffer ----------

def test_start_exactly_buffer_after_existing_end_is_allowed():
    assert can_book([(at(10), at(11))], at(11, 15), at(12), buffer_minutes=15) is True


def test_start_one_minute_inside_buffer_is_rejected():
    assert can_book([(at(10), at(11))], at(11, 14), at(12), buffer_minutes=15) is False


def test_end_exactly_buffer_before_existing_start_is_allowed():
    assert can_book([(at(10), at(11))], at(9), at(9, 45), buffer_minutes=15) is True


def test_end_one_minute_inside_buffer_before_existing_is_rejected():
    assert can_book([(at(10), at(11))], at(9, 1), at(9, 50), buffer_minutes=15) is False


def test_overlap_is_rejected_with_buffer():
    assert can_book([(at(10), at(11))], at(9), at(10), buffer_minutes=15) is False


def test_buffer_of_one_minute_rejects_back_to_back():
    assert can_book([(at(10), at(11))], at(11), at(12), buffer_minutes=1) is False


def test_buffer_is_measured_from_both_sides_of_later_booking():
    existing = [(at(12), at(13))]
    assert can_book(existing, at(10), at(11, 30), buffer_minutes=30) is True
    assert can_book(existing, at(10), at(11, 31), buffer_minutes=30) is False


# ---------- merge_intervals ----------

def test_merge_of_empty_list_is_empty():
    assert merge_intervals([]) == []


def test_merge_single_interval_is_unchanged():
    assert merge_intervals([(at(8), at(9))]) == [(at(8), at(9))]


def test_disjoint_intervals_are_kept_in_order():
    assert merge_intervals([(at(8), at(9)), (at(10), at(11))]) == [(at(8), at(9)), (at(10), at(11))]


def test_unsorted_disjoint_intervals_are_sorted():
    assert merge_intervals([(at(12), at(13)), (at(8), at(9))]) == [(at(8), at(9)), (at(12), at(13))]


def test_overlapping_intervals_are_merged():
    assert merge_intervals([(at(8), at(10)), (at(9), at(11))]) == [(at(8), at(11))]


def test_touching_intervals_are_merged():
    assert merge_intervals([(at(8), at(10)), (at(10), at(11))]) == [(at(8), at(11))]


def test_nested_interval_does_not_shrink_result():
    assert merge_intervals([(at(8), at(12)), (at(9), at(10))]) == [(at(8), at(12))]


def test_nested_interval_given_second_does_not_shrink_result():
    assert merge_intervals([(at(9), at(10)), (at(8), at(12))]) == [(at(8), at(12))]


def test_chain_of_touching_intervals_merges_into_one():
    assert merge_intervals([(at(8), at(9)), (at(9), at(10)), (at(10), at(11))]) == [(at(8), at(11))]


def test_multiple_groups_are_merged_independently():
    result = merge_intervals([(at(13), at(14)), (at(8), at(9)), (at(8), at(10)), (at(12), at(13))])
    assert result == [(at(8), at(10)), (at(12), at(14))]


def test_zero_length_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(8), at(8))])


def test_reversed_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(9), at(8))])


def test_invalid_interval_among_valid_ones_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(8), at(9)), (at(11), at(10))])


def test_input_list_is_not_modified():
    intervals = [(at(12), at(13)), (at(8), at(10)), (at(9), at(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_result_is_a_new_list():
    intervals = [(at(8), at(9))]
    result = merge_intervals(intervals)
    assert result is not intervals
    assert result == intervals
