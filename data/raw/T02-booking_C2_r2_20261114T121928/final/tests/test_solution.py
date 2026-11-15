from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=1):
    return datetime(2026, 1, day, hour, minute)


# ---------- can_book ----------

def test_empty_room_accepts_valid_booking():
    assert can_book([], dt(10), dt(11)) is True


def test_invalid_order_raises():
    with pytest.raises(ValueError):
        can_book([], dt(11), dt(10))


def test_zero_length_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(11), buffer_minutes=-1)


def test_zero_buffer_is_allowed():
    assert can_book([], dt(10), dt(11), buffer_minutes=0) is True


def test_different_days_rejected():
    assert can_book([], dt(17, day=1), dt(9, day=2)) is False


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
    assert can_book([], dt(6), dt(7), open_time=time(6, 0), close_time=time(7, 0)) is True
    assert can_book([], dt(5), dt(6), open_time=time(6, 0), close_time=time(7, 0)) is False
    assert can_book([], dt(7), dt(8), open_time=time(6, 0), close_time=time(7, 0)) is False


def test_overlap_at_start_rejected():
    assert can_book([(dt(9), dt(11))], dt(10), dt(12)) is False


def test_overlap_at_end_rejected():
    assert can_book([(dt(10), dt(12))], dt(9), dt(11)) is False


def test_new_booking_inside_existing_rejected():
    assert can_book([(dt(9), dt(12))], dt(10), dt(11)) is False


def test_existing_inside_new_rejected():
    assert can_book([(dt(10), dt(11))], dt(9), dt(12)) is False


def test_back_to_back_allowed_with_zero_buffer():
    assert can_book([(dt(10), dt(11))], dt(11), dt(12)) is True


def test_back_to_back_before_allowed_with_zero_buffer():
    assert can_book([(dt(11), dt(12))], dt(10), dt(11)) is True


def test_adjacent_without_buffer_rejected_when_buffer_positive():
    assert can_book([(dt(10), dt(11))], dt(11), dt(12), buffer_minutes=1) is False


def test_buffer_after_existing_exact_gap_allowed():
    assert can_book([(dt(10), dt(11))], dt(11, 15), dt(12), buffer_minutes=15) is True


def test_buffer_after_existing_short_gap_rejected():
    assert can_book([(dt(10), dt(11))], dt(11, 14), dt(12), buffer_minutes=15) is False


def test_buffer_before_existing_exact_gap_allowed():
    assert can_book([(dt(12), dt(13))], dt(10), dt(11, 45), buffer_minutes=15) is True


def test_buffer_before_existing_short_gap_rejected():
    assert can_book([(dt(12), dt(13))], dt(10), dt(11, 46), buffer_minutes=15) is False


def test_booking_not_conflicting_with_any_of_many():
    existing = [(dt(8), dt(9)), (dt(10), dt(11)), (dt(13), dt(14))]
    assert can_book(existing, dt(11), dt(13)) is True
    assert can_book(existing, dt(11), dt(13, 30)) is False


def test_existing_list_not_mutated_by_can_book():
    existing = [(dt(8), dt(9))]
    can_book(existing, dt(10), dt(11))
    assert existing == [(dt(8), dt(9))]


# ---------- merge_intervals ----------

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_sorts_disjoint_intervals():
    assert merge_intervals([(dt(13), dt(14)), (dt(9), dt(10))]) == [(dt(9), dt(10)), (dt(13), dt(14))]


def test_merge_overlapping():
    assert merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))]) == [(dt(9), dt(12))]


def test_merge_touching_intervals():
    assert merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))]) == [(dt(9), dt(11))]


def test_merge_contained_interval_keeps_outer_end():
    assert merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))]) == [(dt(9), dt(12))]


def test_merge_contained_interval_listed_first():
    assert merge_intervals([(dt(10), dt(11)), (dt(9), dt(12))]) == [(dt(9), dt(12))]


def test_merge_chain_of_overlaps():
    intervals = [(dt(14), dt(15)), (dt(9), dt(10)), (dt(9, 30), dt(11)), (dt(10, 30), dt(12))]
    assert merge_intervals(intervals) == [(dt(9), dt(12)), (dt(14), dt(15))]


def test_merge_gap_not_merged():
    assert merge_intervals([(dt(9), dt(10)), (dt(10, 1), dt(11))]) == [(dt(9), dt(10)), (dt(10, 1), dt(11))]


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(10)), (dt(12), dt(11))])


def test_merge_zero_length_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(9))])


def test_merge_does_not_modify_input():
    intervals = [(dt(13), dt(14)), (dt(9), dt(10)), (dt(9, 30), dt(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot
