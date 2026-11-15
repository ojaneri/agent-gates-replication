import os
import sys
from datetime import datetime, time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from solution import can_book, merge_intervals  # noqa: E402


def dt(h, m=0, day=1):
    return datetime(2024, 3, day, h, m)


# ---------- can_book ----------

def test_free_room_booking_allowed():
    assert can_book([], dt(10), dt(11)) is True


def test_end_before_or_equal_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(11), dt(10))
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(11), buffer_minutes=-1)


def test_zero_buffer_allowed_is_not_negative():
    assert can_book([], dt(10), dt(11), buffer_minutes=0) is True


def test_different_days_rejected():
    assert can_book([], datetime(2024, 3, 1, 17, 0), datetime(2024, 3, 2, 9, 0)) is False


def test_exactly_four_hours_allowed():
    assert can_book([], dt(8), dt(12)) is True


def test_more_than_four_hours_rejected():
    assert can_book([], dt(8), dt(12, 1)) is False


def test_start_exactly_at_open_allowed():
    assert can_book([], dt(8), dt(9)) is True


def test_start_before_open_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_end_exactly_at_close_allowed():
    assert can_book([], dt(17), dt(18)) is True


def test_end_after_close_rejected():
    assert can_book([], dt(17), dt(18, 1)) is False


def test_custom_open_and_close_times():
    assert can_book([], dt(7), dt(8), open_time=time(7, 0), close_time=time(20, 0)) is True
    assert can_book([], dt(6, 30), dt(7), open_time=time(7, 0), close_time=time(20, 0)) is False
    assert can_book([], dt(19), dt(20, 30), open_time=time(7, 0), close_time=time(20, 0)) is False


def test_overlap_with_existing_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(10, 30), dt(11, 30)) is False
    assert can_book(existing, dt(9, 30), dt(10, 30)) is False
    assert can_book(existing, dt(9), dt(12)) is False
    assert can_book(existing, dt(10, 15), dt(10, 45)) is False


def test_booking_contained_in_existing_rejected():
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
    assert can_book(existing, dt(8, 0), dt(9, 45), buffer_minutes=15) is True


def test_buffer_one_minute_short_rejected():
    existing = [(dt(10), dt(11))]
    assert can_book(existing, dt(11, 14), dt(12), buffer_minutes=15) is False
    assert can_book(existing, dt(8, 0), dt(9, 46), buffer_minutes=15) is False


def test_buffer_applies_against_multiple_existing():
    existing = [(dt(9), dt(10)), (dt(12), dt(13))]
    assert can_book(existing, dt(10, 30), dt(11), buffer_minutes=30) is True
    assert can_book(existing, dt(10, 30), dt(11), buffer_minutes=31) is False


# ---------- merge_intervals ----------

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(dt(9), dt(10))]) == [(dt(9), dt(10))]


def test_merge_sorts_unordered_disjoint():
    result = merge_intervals([(dt(12), dt(13)), (dt(9), dt(10))])
    assert result == [(dt(9), dt(10)), (dt(12), dt(13))]


def test_merge_overlapping():
    result = merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))])
    assert result == [(dt(9), dt(12))]


def test_merge_contained():
    result = merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(12))]


def test_merge_touching_intervals():
    result = merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(11))]


def test_merge_chain_of_overlaps():
    result = merge_intervals([(dt(13), dt(14)), (dt(9), dt(10)), (dt(9, 30), dt(11)), (dt(10, 30), dt(13))])
    assert result == [(dt(9), dt(14))]


def test_merge_does_not_modify_input():
    original = [(dt(12), dt(13)), (dt(9), dt(10)), (dt(9, 30), dt(11))]
    snapshot = list(original)
    merge_intervals(original)
    assert original == snapshot


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(9))])
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(9))])
