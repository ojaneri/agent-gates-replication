from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=14):
    return datetime(2026, 11, day, hour, minute)


# ---------- can_book: argument validation ----------

def test_end_equal_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10))


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(11), dt(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(11), buffer_minutes=-1)


def test_zero_buffer_is_accepted():
    assert can_book([], dt(10), dt(11), buffer_minutes=0) is True


def test_invalid_end_checked_before_negative_buffer():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10), buffer_minutes=-5)


# ---------- can_book: same calendar day ----------

def test_crossing_midnight_is_rejected():
    start = datetime(2026, 11, 14, 17, 0)
    end = datetime(2026, 11, 15, 1, 0)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59)) is False


def test_same_day_booking_is_accepted():
    assert can_book([], dt(9), dt(10)) is True


# ---------- can_book: duration ----------

def test_exactly_four_hours_allowed():
    assert can_book([], dt(9), dt(13)) is True


def test_four_hours_and_one_minute_rejected():
    assert can_book([], dt(9), dt(13, 1)) is False


def test_long_booking_rejected_even_when_inside_hours():
    assert can_book([], dt(8), dt(17)) is False


def test_three_hours_fifty_nine_minutes_allowed():
    assert can_book([], dt(9), dt(12, 59)) is True


# ---------- can_book: opening hours ----------

def test_start_before_open_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_start_exactly_at_open_allowed():
    assert can_book([], dt(8), dt(9)) is True


def test_end_after_close_rejected():
    assert can_book([], dt(17), dt(18, 1)) is False


def test_end_exactly_at_close_allowed():
    assert can_book([], dt(17), dt(18)) is True


def test_custom_open_and_close_times():
    assert can_book([], dt(7), dt(8), open_time=time(7, 0), close_time=time(9, 0)) is True
    assert can_book([], dt(6, 30), dt(7), open_time=time(7, 0), close_time=time(9, 0)) is False
    assert can_book([], dt(8, 30), dt(9, 30), open_time=time(7, 0), close_time=time(9, 0)) is False


def test_default_open_time_is_eight():
    assert can_book([], dt(7, 30), dt(8, 30)) is False
    assert can_book([], dt(8, 0), dt(8, 30)) is True


def test_default_close_time_is_eighteen():
    assert can_book([], dt(17, 30), dt(18, 0)) is True
    assert can_book([], dt(17, 30), dt(18, 15)) is False


# ---------- can_book: conflicts with zero buffer ----------

def test_no_existing_bookings_is_free():
    assert can_book([], dt(10), dt(11)) is True


def test_identical_booking_conflicts():
    assert can_book([(dt(10), dt(11))], dt(10), dt(11)) is False


def test_overlap_at_start_conflicts():
    assert can_book([(dt(10), dt(11))], dt(9), dt(10, 30)) is False


def test_overlap_at_end_conflicts():
    assert can_book([(dt(10), dt(11))], dt(10, 30), dt(11, 30)) is False


def test_new_booking_inside_existing_conflicts():
    assert can_book([(dt(9), dt(12))], dt(10), dt(11)) is False


def test_new_booking_containing_existing_conflicts():
    assert can_book([(dt(10), dt(11))], dt(9), dt(12)) is False


def test_back_to_back_after_is_allowed():
    assert can_book([(dt(10), dt(11))], dt(11), dt(12)) is True


def test_back_to_back_before_is_allowed():
    assert can_book([(dt(10), dt(11))], dt(9), dt(10)) is True


def test_one_minute_overlap_conflicts():
    assert can_book([(dt(10), dt(11))], dt(10, 59), dt(12)) is False


def test_disjoint_booking_is_allowed():
    assert can_book([(dt(10), dt(11))], dt(12), dt(13)) is True


def test_conflict_detected_with_later_existing_entry():
    existing = [(dt(8), dt(9)), (dt(9, 30), dt(10)), (dt(14), dt(15))]
    assert can_book(existing, dt(9, 45), dt(10, 30)) is False
    assert can_book(existing, dt(10), dt(14)) is True


def test_empty_existing_list_with_many_entries_order_independent():
    existing = [(dt(14), dt(15)), (dt(8), dt(9))]
    assert can_book(existing, dt(10), dt(11)) is True


# ---------- can_book: buffers ----------

def test_buffer_blocks_start_too_close_after_existing():
    # existing ends 11:00, 15 min buffer, new starts 11:10 -> too close
    assert can_book([(dt(10), dt(11))], dt(11, 10), dt(12), buffer_minutes=15) is False


def test_buffer_allows_start_exactly_buffer_after_existing():
    assert can_book([(dt(10), dt(11))], dt(11, 15), dt(12), buffer_minutes=15) is True


def test_buffer_blocks_end_too_close_before_existing():
    # new ends 9:50, existing starts 10:00, buffer 15 -> too close
    assert can_book([(dt(10), dt(11))], dt(9), dt(9, 50), buffer_minutes=15) is False


def test_buffer_allows_end_exactly_buffer_before_existing():
    assert can_book([(dt(10), dt(11))], dt(9), dt(9, 45), buffer_minutes=15) is True


def test_buffer_one_minute_short_is_rejected():
    assert can_book([(dt(10), dt(11))], dt(11, 14), dt(12), buffer_minutes=15) is False


def test_buffer_applies_to_both_sides_of_same_existing():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11, 5), dt(11, 30), buffer_minutes=10) is False
    assert can_book(existing, dt(9, 20), dt(9, 55), buffer_minutes=10) is False
    assert can_book(existing, dt(9, 20), dt(9, 50), buffer_minutes=10) is True


def test_buffer_with_overlap_still_conflicts():
    assert can_book([(dt(10), dt(11))], dt(10, 30), dt(11, 30), buffer_minutes=5) is False


def test_buffer_zero_allows_back_to_back_but_positive_does_not():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11), dt(12), buffer_minutes=0) is True
    assert can_book(existing, dt(11), dt(12), buffer_minutes=1) is False


def test_buffer_allows_booking_with_ample_gap():
    existing = [(dt(9), dt(10)), (dt(13), dt(14))]
    assert can_book(existing, dt(11), dt(12), buffer_minutes=30) is True


def test_buffer_checks_every_existing_booking():
    existing = [(dt(9), dt(10)), (dt(10, 30), dt(11))]
    # 10:10 start is 10 min after the 10:00 end; with buffer 20 it conflicts with the first one
    assert can_book(existing, dt(10, 10), dt(10, 20), buffer_minutes=20) is False


# ---------- merge_intervals ----------

def test_merge_empty_list():
    assert merge_intervals([]) == []


def test_merge_single_interval():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_disjoint_sorted_output():
    result = merge_intervals([(dt(13), dt(14)), (dt(9), dt(10))])
    assert result == [(dt(9), dt(10)), (dt(13), dt(14))]


def test_merge_overlapping():
    result = merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))])
    assert result == [(dt(9), dt(12))]


def test_merge_touching_intervals():
    result = merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(11))]


def test_merge_contained_interval():
    result = merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(12))]


def test_merge_contained_interval_order_reversed():
    result = merge_intervals([(dt(10), dt(11)), (dt(9), dt(12))])
    assert result == [(dt(9), dt(12))]


def test_merge_one_minute_gap_not_merged():
    result = merge_intervals([(dt(9), dt(10)), (dt(10, 1), dt(11))])
    assert result == [(dt(9), dt(10)), (dt(10, 1), dt(11))]


def test_merge_chain_of_overlaps():
    intervals = [(dt(12), dt(13)), (dt(9), dt(10)), (dt(9, 30), dt(11)), (dt(10, 30), dt(12, 30))]
    assert merge_intervals(intervals) == [(dt(9), dt(13))]


def test_merge_does_not_modify_input():
    intervals = [(dt(12), dt(13)), (dt(9), dt(10)), (dt(9, 30), dt(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_returns_new_list():
    intervals = [(dt(9), dt(10))]
    result = merge_intervals(intervals)
    assert result is not intervals


def test_merge_invalid_zero_length_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(9))])


def test_merge_invalid_reversed_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(9))])


def test_merge_invalid_among_valid_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(10)), (dt(12), dt(11))])


def test_merge_unsorted_with_multiple_groups():
    intervals = [(dt(15), dt(16)), (dt(9), dt(10)), (dt(15, 30), dt(17)), (dt(10), dt(11)), (dt(8), dt(8, 30))]
    assert merge_intervals(intervals) == [
        (dt(8), dt(8, 30)),
        (dt(9), dt(11)),
        (dt(15), dt(17)),
    ]
