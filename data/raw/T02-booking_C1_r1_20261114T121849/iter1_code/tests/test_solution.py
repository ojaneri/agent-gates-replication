from datetime import datetime, time

import pytest

from solution import can_book, merge_intervals


def dt(hour, minute=0, day=14):
    return datetime(2026, 11, day, hour, minute)


# ---- can_book ----

def test_free_room_allows_booking():
    assert can_book([], dt(10), dt(11)) is True


def test_end_not_after_start_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(10))
    with pytest.raises(ValueError):
        can_book([], dt(11), dt(10))


def test_negative_buffer_raises():
    with pytest.raises(ValueError):
        can_book([], dt(10), dt(11), buffer_minutes=-1)


def test_zero_buffer_is_allowed():
    assert can_book([], dt(10), dt(11), buffer_minutes=0) is True


def test_different_calendar_days_rejected():
    assert can_book([], datetime(2026, 11, 14, 17, 0), datetime(2026, 11, 15, 9, 0),
                    open_time=time(0, 0), close_time=time(23, 59)) is False


def test_exactly_four_hours_allowed():
    assert can_book([], dt(8), dt(12)) is True


def test_longer_than_four_hours_rejected():
    assert can_book([], dt(8), dt(12, 1)) is False


def test_starts_before_open_rejected():
    assert can_book([], dt(7, 59), dt(9)) is False


def test_starts_exactly_at_open_allowed():
    assert can_book([], dt(8), dt(9)) is True


def test_ends_after_close_rejected():
    assert can_book([], dt(17), dt(18, 1)) is False


def test_ends_exactly_at_close_allowed():
    assert can_book([], dt(17), dt(18)) is True


def test_custom_open_and_close_times():
    assert can_book([], dt(7), dt(8), open_time=time(7, 0), close_time=time(9, 0)) is True
    assert can_book([], dt(6, 30), dt(7, 30), open_time=time(7, 0), close_time=time(9, 0)) is False
    assert can_book([], dt(8, 30), dt(9, 30), open_time=time(7, 0), close_time=time(9, 0)) is False


def test_overlap_with_existing_rejected():
    assert can_book([(dt(10), dt(11))], dt(10, 30), dt(11, 30)) is False


def test_contained_within_existing_rejected():
    assert can_book([(dt(9), dt(12))], dt(10), dt(11)) is False


def test_containing_existing_rejected():
    assert can_book([(dt(10), dt(11))], dt(9), dt(12)) is False


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


def test_buffer_applies_to_every_existing_booking():
    existing = [(dt(9), dt(9, 30)), (dt(10), dt(11))]
    assert can_book(existing, dt(11, 30), dt(12), buffer_minutes=15) is True
    assert can_book(existing, dt(9, 40), dt(9, 50), buffer_minutes=15) is False


def test_empty_existing_ignores_buffer():
    assert can_book([], dt(10), dt(11), buffer_minutes=60) is True


# ---- merge_intervals ----

def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_single():
    assert merge_intervals([(dt(10), dt(11))]) == [(dt(10), dt(11))]


def test_merge_sorts_disjoint_intervals():
    result = merge_intervals([(dt(14), dt(15)), (dt(9), dt(10))])
    assert result == [(dt(9), dt(10)), (dt(14), dt(15))]


def test_merge_overlapping():
    result = merge_intervals([(dt(9), dt(11)), (dt(10), dt(12))])
    assert result == [(dt(9), dt(12))]


def test_merge_touching_intervals():
    result = merge_intervals([(dt(9), dt(10)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(11))]


def test_merge_contained_interval():
    result = merge_intervals([(dt(9), dt(12)), (dt(10), dt(11))])
    assert result == [(dt(9), dt(12))]


def test_merge_chain_in_unsorted_order():
    result = merge_intervals([(dt(12), dt(13)), (dt(9), dt(10)), (dt(10), dt(11)), (dt(11), dt(12))])
    assert result == [(dt(9), dt(13))]


def test_merge_does_not_modify_input():
    data = [(dt(12), dt(13)), (dt(9), dt(10))]
    snapshot = list(data)
    merge_intervals(data)
    assert data == snapshot


def test_merge_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(dt(10), dt(10))])
    with pytest.raises(ValueError):
        merge_intervals([(dt(9), dt(10)), (dt(12), dt(11))])
