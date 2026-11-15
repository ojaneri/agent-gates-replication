import datetime as dt
from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def d(h, m=0, day=14):
    return datetime(2026, 11, day, h, m)


# ---------- can_book ----------

def test_free_room_books():
    assert can_book([], d(10), d(11)) is True


def test_end_before_start_raises():
    with pytest.raises(ValueError):
        can_book([], d(11), d(10))


def test_end_equal_start_raises():
    with pytest.raises(ValueError):
        can_book([], d(10), d(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], d(10), d(11), buffer_minutes=-1)


def test_zero_buffer_is_allowed():
    assert can_book([], d(10), d(11), buffer_minutes=0) is True


def test_different_days_rejected():
    start = datetime(2026, 11, 14, 17, 0)
    end = datetime(2026, 11, 15, 9, 0)
    assert can_book([], start, end, open_time=time(0, 0), close_time=time(23, 59)) is False


def test_exactly_four_hours_allowed():
    assert can_book([], d(8), d(12)) is True


def test_longer_than_four_hours_rejected():
    assert can_book([], d(8), d(12, 1)) is False


def test_start_before_open_rejected():
    assert can_book([], d(7, 59), d(9)) is False


def test_start_at_open_allowed():
    assert can_book([], d(8), d(9)) is True


def test_end_after_close_rejected():
    assert can_book([], d(17), d(18, 1)) is False


def test_end_at_close_allowed():
    assert can_book([], d(17), d(18)) is True


def test_custom_open_and_close_times():
    assert can_book([], d(7), d(8), open_time=time(7, 0)) is True
    assert can_book([], d(19), d(20), close_time=time(20, 0)) is True
    assert can_book([], d(6), d(7), open_time=time(7, 0)) is False
    assert can_book([], d(19), d(21), close_time=time(20, 0)) is False


def test_overlap_rejected():
    assert can_book([(d(10), d(11))], d(10, 30), d(11, 30)) is False


def test_contained_booking_rejected():
    assert can_book([(d(9), d(12))], d(10), d(11)) is False


def test_containing_booking_rejected():
    assert can_book([(d(10), d(11))], d(9), d(12)) is False


def test_identical_booking_rejected():
    assert can_book([(d(10), d(11))], d(10), d(11)) is False


def test_back_to_back_after_allowed_with_zero_buffer():
    assert can_book([(d(10), d(11))], d(11), d(12)) is True


def test_back_to_back_before_allowed_with_zero_buffer():
    assert can_book([(d(10), d(11))], d(9), d(10)) is True


def test_half_open_no_overlap_at_boundary():
    assert can_book([(d(10), d(11))], d(9), d(10, 1)) is False


def test_buffer_blocks_back_to_back_after():
    assert can_book([(d(10), d(11))], d(11), d(12), buffer_minutes=15) is False


def test_buffer_exactly_met_after_allowed():
    assert can_book([(d(10), d(11))], d(11, 15), d(12), buffer_minutes=15) is True


def test_buffer_blocks_back_to_back_before():
    assert can_book([(d(10), d(11))], d(9), d(10), buffer_minutes=15) is False


def test_buffer_exactly_met_before_allowed():
    assert can_book([(d(10), d(11))], d(9), d(9, 45), buffer_minutes=15) is True


def test_buffer_ignores_far_bookings():
    assert can_book([(d(14), d(15))], d(10), d(11), buffer_minutes=30) is True


def test_multiple_existing_bookings_checked():
    existing = [(d(8), d(9)), (d(10), d(11)), (d(13), d(14))]
    assert can_book(existing, d(9), d(10)) is True
    assert can_book(existing, d(11), d(13)) is True
    assert can_book(existing, d(11), d(13, 30)) is False


def test_existing_unsorted_still_detects_conflict():
    existing = [(d(13), d(14)), (d(8), d(9)), (d(10), d(12))]
    assert can_book(existing, d(11), d(11, 30)) is False


def test_validation_precedes_other_rules():
    # end <= start raises even though the booking would also be out of hours
    with pytest.raises(ValueError):
        can_book([], d(20), d(19))


# ---------- merge_intervals ----------

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(d(10), d(11))]) == [(d(10), d(11))]


def test_merge_disjoint_sorted_output():
    result = merge_intervals([(d(13), d(14)), (d(8), d(9))])
    assert result == [(d(8), d(9)), (d(13), d(14))]


def test_merge_overlapping():
    assert merge_intervals([(d(8), d(10)), (d(9), d(11))]) == [(d(8), d(11))]


def test_merge_touching_intervals():
    assert merge_intervals([(d(8), d(9)), (d(9), d(10))]) == [(d(8), d(10))]


def test_merge_contained_interval():
    assert merge_intervals([(d(8), d(12)), (d(9), d(10))]) == [(d(8), d(12))]


def test_merge_chain_of_overlaps():
    intervals = [(d(10), d(11)), (d(8), d(9)), (d(9, 30), d(10, 30)), (d(12), d(13))]
    assert merge_intervals(intervals) == [(d(8), d(9)), (d(9, 30), d(11)), (d(12), d(13))]


def test_merge_chain_bridges_into_one():
    intervals = [(d(8), d(9)), (d(9), d(10)), (d(9, 30), d(11)), (d(10, 30), d(12))]
    assert merge_intervals(intervals) == [(d(8), d(12))]


def test_merge_does_not_modify_input():
    intervals = [(d(13), d(14)), (d(8), d(10)), (d(9), d(11))]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(d(8), d(9)), (d(10), d(10))])
    with pytest.raises(ValueError):
        merge_intervals([(d(11), d(10))])
