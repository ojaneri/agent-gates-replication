from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals

DAY = (2026, 11, 14)


def at(hour, minute=0, day=DAY):
    return datetime(day[0], day[1], day[2], hour, minute)


# ---------------------------------------------------------------- can_book: validation

def test_end_equal_to_start_raises():
    with pytest.raises(ValueError):
        can_book([], at(10), at(10))


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], at(11), at(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], at(10), at(11), buffer_minutes=-1)


def test_validation_raises_even_when_other_rules_would_reject():
    with pytest.raises(ValueError):
        can_book([], at(10), at(10), buffer_minutes=-5)


def test_zero_buffer_is_allowed():
    assert can_book([], at(10), at(11), buffer_minutes=0) is True


# ---------------------------------------------------------------- can_book: empty room / basics

def test_empty_room_accepts_booking():
    assert can_book([], at(10), at(11)) is True


def test_returns_bool_true_not_truthy_value():
    assert can_book([(at(9), at(10))], at(11), at(12)) is True


# ---------------------------------------------------------------- can_book: same day

def test_booking_crossing_midnight_is_rejected():
    start = datetime(2026, 11, 14, 23, 0)
    end = datetime(2026, 11, 15, 0, 30)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59)) is False


def test_booking_starting_on_previous_day_is_rejected():
    start = datetime(2026, 11, 13, 9, 0)
    end = datetime(2026, 11, 14, 9, 0)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59)) is False


# ---------------------------------------------------------------- can_book: duration

def test_exactly_four_hours_is_allowed():
    assert can_book([], at(8), at(12)) is True


def test_four_hours_and_one_minute_is_rejected():
    assert can_book([], at(8), at(12, 1)) is False


def test_long_booking_rejected_with_wide_hours():
    assert can_book([], at(6), at(12, 1), open_time=time(0, 0), close_time=time(23, 59)) is False


def test_four_hours_allowed_with_wide_hours():
    assert can_book([], at(6), at(10), open_time=time(0, 0), close_time=time(23, 59)) is True


# ---------------------------------------------------------------- can_book: opening hours

def test_start_exactly_at_default_open_is_allowed():
    assert can_book([], at(8), at(9)) is True


def test_start_one_minute_before_default_open_is_rejected():
    assert can_book([], at(7, 59), at(9)) is False


def test_end_exactly_at_default_close_is_allowed():
    assert can_book([], at(17), at(18)) is True


def test_end_one_minute_after_default_close_is_rejected():
    assert can_book([], at(17, 30), at(18, 1)) is False


def test_custom_open_and_close_times_are_used():
    assert can_book([], at(9), at(10), open_time=time(9), close_time=time(10)) is True
    assert can_book([], at(8), at(9), open_time=time(9), close_time=time(10)) is False
    assert can_book([], at(9), at(10, 1), open_time=time(9), close_time=time(10)) is False


def test_custom_open_time_allows_earlier_start_when_lowered():
    assert can_book([], at(6), at(7), open_time=time(5), close_time=time(18)) is True


# ---------------------------------------------------------------- can_book: conflicts (buffer 0)

def test_overlap_at_end_conflicts():
    assert can_book([(at(10), at(11))], at(10, 30), at(11, 30)) is False


def test_overlap_at_start_conflicts():
    assert can_book([(at(10), at(11))], at(9, 30), at(10, 30)) is False


def test_new_booking_inside_existing_conflicts():
    assert can_book([(at(9), at(12))], at(10), at(11)) is False


def test_new_booking_enclosing_existing_conflicts():
    assert can_book([(at(10), at(11))], at(9), at(12)) is False


def test_identical_booking_conflicts():
    assert can_book([(at(10), at(11))], at(10), at(11)) is False


def test_back_to_back_after_existing_is_allowed():
    assert can_book([(at(10), at(11))], at(11), at(12)) is True


def test_back_to_back_before_existing_is_allowed():
    assert can_book([(at(11), at(12))], at(10), at(11)) is True


def test_disjoint_booking_is_allowed():
    assert can_book([(at(9), at(10))], at(13), at(14)) is True


def test_conflict_detected_among_several_existing():
    existing = [(at(8), at(9)), (at(10), at(11)), (at(14), at(15))]
    assert can_book(existing, at(10, 30), at(11, 30)) is False


def test_gap_between_several_existing_is_allowed():
    existing = [(at(8), at(9)), (at(10), at(11)), (at(14), at(15))]
    assert can_book(existing, at(11), at(12)) is True


def test_conflict_with_later_entry_in_list_detected():
    existing = [(at(14), at(15)), (at(10), at(11))]
    assert can_book(existing, at(10), at(10, 30)) is False


# ---------------------------------------------------------------- can_book: buffers

def test_buffer_after_existing_too_close_rejected():
    assert can_book([(at(10), at(11))], at(11, 10), at(12), buffer_minutes=15) is False


def test_buffer_after_existing_exact_allowed():
    assert can_book([(at(10), at(11))], at(11, 15), at(12), buffer_minutes=15) is True


def test_buffer_before_existing_too_close_rejected():
    assert can_book([(at(13), at(14))], at(12), at(12, 50), buffer_minutes=15) is False


def test_buffer_before_existing_exact_allowed():
    assert can_book([(at(13), at(14))], at(12), at(12, 45), buffer_minutes=15) is True


def test_large_buffer_rejects_nearby_booking():
    assert can_book([(at(10), at(11))], at(11, 30), at(12), buffer_minutes=60) is False


def test_buffer_does_not_affect_distant_bookings():
    assert can_book([(at(9), at(10))], at(14), at(15), buffer_minutes=60) is True


def test_buffer_applies_to_overlapping_bookings():
    assert can_book([(at(10), at(11))], at(10, 30), at(11, 30), buffer_minutes=5) is False


def test_buffer_one_minute_gap_with_buffer_two_rejected():
    assert can_book([(at(10), at(11))], at(11, 1), at(12), buffer_minutes=2) is False


def test_buffer_one_minute_gap_with_buffer_one_allowed():
    assert can_book([(at(10), at(11))], at(11, 1), at(12), buffer_minutes=1) is True


def test_empty_room_with_buffer_accepts_booking():
    assert can_book([], at(10), at(11), buffer_minutes=30) is True


# ---------------------------------------------------------------- merge_intervals

def test_merge_empty_list_returns_empty_list():
    assert merge_intervals([]) == []


def test_merge_single_interval():
    assert merge_intervals([(at(9), at(10))]) == [(at(9), at(10))]


def test_merge_disjoint_intervals_kept_in_order():
    intervals = [(at(13), at(14)), (at(9), at(10))]
    assert merge_intervals(intervals) == [(at(9), at(10)), (at(13), at(14))]


def test_merge_overlapping_intervals():
    assert merge_intervals([(at(9), at(11)), (at(10), at(12))]) == [(at(9), at(12))]


def test_merge_touching_intervals():
    assert merge_intervals([(at(9), at(10)), (at(10), at(11))]) == [(at(9), at(11))]


def test_merge_contained_interval_keeps_outer_end():
    assert merge_intervals([(at(9), at(17)), (at(10), at(11))]) == [(at(9), at(17))]


def test_merge_same_start_keeps_longer_end():
    assert merge_intervals([(at(9), at(10)), (at(9), at(12))]) == [(at(9), at(12))]


def test_merge_unsorted_input():
    intervals = [(at(14), at(15)), (at(9), at(10)), (at(10), at(11)), (at(9, 30), at(12))]
    assert merge_intervals(intervals) == [(at(9), at(12)), (at(14), at(15))]


def test_merge_chain_of_touching_intervals():
    intervals = [(at(8), at(9)), (at(9), at(10)), (at(10), at(11))]
    assert merge_intervals(intervals) == [(at(8), at(11))]


def test_merge_unsorted_containment_needs_start_sorting():
    intervals = [(at(5), at(6)), (at(2), at(3)), (at(1), at(10))]
    assert merge_intervals(intervals) == [(at(1), at(10))]


def test_merge_gap_is_not_merged():
    assert merge_intervals([(at(9), at(10)), (at(10, 1), at(11))]) == [(at(9), at(10)), (at(10, 1), at(11))]


def test_merge_does_not_modify_input():
    intervals = [(at(14), at(15)), (at(9), at(10)), (at(9, 30), at(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_returns_new_list():
    intervals = [(at(9), at(10))]
    result = merge_intervals(intervals)
    assert result is not intervals
    assert result == intervals


def test_merge_result_items_are_tuples():
    result = merge_intervals([(at(9), at(10)), (at(10), at(11))])
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)


def test_merge_zero_length_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(9), at(9))])


def test_merge_reversed_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(10), at(9))])


def test_merge_invalid_interval_among_valid_raises():
    with pytest.raises(ValueError):
        merge_intervals([(at(9), at(10)), (at(12), at(11))])
