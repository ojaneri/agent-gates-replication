from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=1):
    return datetime(2024, 3, day, hour, minute)


# ---------- can_book ----------

def test_simple_booking_allowed():
    assert can_book([], dt(10), dt(11)) is True


def test_end_not_after_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(11), dt(11))
    with pytest.raises(ValueError):
        can_book([], dt(12), dt(11))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(11), buffer_minutes=-1)


def test_zero_buffer_is_allowed():
    assert can_book([], dt(10), dt(11), buffer_minutes=0) is True


def test_different_days_rejected():
    assert can_book([], datetime(2024, 3, 1, 17), datetime(2024, 3, 2, 9)) is False


def test_exactly_four_hours_allowed():
    assert can_book([], dt(9), dt(13)) is True


def test_longer_than_four_hours_rejected():
    assert can_book([], dt(9), dt(13, 1)) is False


def test_open_time_boundary_inclusive():
    assert can_book([], dt(8), dt(9)) is True


def test_before_open_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_close_time_boundary_inclusive():
    assert can_book([], dt(17), dt(18)) is True


def test_after_close_rejected():
    assert can_book([], dt(17, 30), dt(18, 1)) is False


def test_custom_open_close_times():
    assert can_book([], dt(6), dt(7), open_time=time(6, 0), close_time=time(7, 0)) is True
    assert can_book([], dt(5, 59), dt(7), open_time=time(6, 0), close_time=time(7, 0)) is False
    assert can_book([], dt(7), dt(7, 30), open_time=time(6, 0), close_time=time(7, 0)) is False


def test_overlap_with_existing_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10, 30), dt(11, 30)) is False
    assert can_book(existing, dt(9, 30), dt(10, 30)) is False
    assert can_book(existing, dt(9), dt(12)) is False


def test_contained_within_existing_rejected():
    existing = [(dt(9), dt(12))]
    assert can_book(existing, dt(10), dt(11)) is False


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
    assert can_book(existing, dt(8), dt(9, 45), buffer_minutes=15) is True


def test_buffer_one_minute_short_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11, 14), dt(12), buffer_minutes=15) is False
    assert can_book(existing, dt(8), dt(9, 46), buffer_minutes=15) is False


def test_non_conflicting_existing_bookings_ignored():
    existing = [(dt(8), dt(9)), (dt(15), dt(16))]
    assert can_book(existing, dt(10), dt(11)) is True


# ---------- merge_intervals ----------

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_sorts_and_merges_overlaps():
    result = merge_intervals([(dt(12), dt(14)), (dt(9), dt(10)), (dt(9, 30), dt(11))])
    assert result == [(dt(9), dt(11)), (dt(12), dt(14))]


def test_merge_touching_intervals():
    result = merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(11))]


def test_merge_contained_interval():
    result = merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(12))]


def test_merge_disjoint_kept_separate():
    result = merge_intervals([(dt(9), dt(10)), (dt(11), dt(12))])
    assert result == [(dt(9), dt(10)), (dt(11), dt(12))]


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(10))])
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(9))])


def test_merge_does_not_modify_input():
    original = [(dt(12), dt(14)), (dt(9), dt(10)), (dt(9, 30), dt(11))]
    snapshot = list(original)
    merge_intervals(original)
    assert original == snapshot
