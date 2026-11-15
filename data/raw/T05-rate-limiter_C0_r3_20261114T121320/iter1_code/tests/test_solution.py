import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from solution import RateLimiter  # noqa: E402


# ----- construction ---------------------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 1.5, "3", None, True, False])
def test_bad_limit_rejected(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1, -0.5])
def test_bad_window_rejected(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction():
    RateLimiter(1, 0.001)
    RateLimiter(10, 60)


# ----- cost validation --------------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, 2.0, True, "1", None])
def test_bad_cost_rejected_by_all_methods(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


# ----- basic allow / remaining ------------------------------------------------

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0) is False


def test_remaining_tracks_usage_and_does_not_record():
    rl = RateLimiter(5, 10.0)
    assert rl.remaining("a", 0.0) == 5
    assert rl.remaining("a", 0.0) == 5  # reading does not consume
    rl.allow("a", 1.0)
    assert rl.remaining("a", 1.0) == 4
    rl.allow("a", 1.0, 2)
    assert rl.remaining("a", 1.0) == 2


def test_weighted_cost():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, 3)
    assert rl.allow("a", 0.0, 3) is False  # 3 + 3 > 5
    assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0, 2)
    assert rl.remaining("a", 0.0) == 0


# ----- rejected requests use no budget ---------------------------------------

def test_rejected_requests_record_nothing():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0, 2)
    for _ in range(5):
        assert rl.allow("a", 1.0) is False
    # Only the first request counts; it expires at t=10.
    assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.allow("a", 10.0)  # the rejected attempts did not extend the block


def test_rejected_weighted_request_uses_no_budget():
    rl = RateLimiter(4, 10.0)
    assert rl.allow("a", 0.0, 3)
    assert rl.allow("a", 0.0, 2) is False
    assert rl.remaining("a", 0.0) == 1
    assert rl.allow("a", 0.0, 1)


# ----- clients are independent -----------------------------------------------

def test_clients_have_separate_budgets():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0)
    assert rl.remaining("c", 0.0) == 1
    assert rl.retry_after("c", 0.0) == 0.0


# ----- sliding window expiry --------------------------------------------------

def test_request_expires_exactly_at_window_boundary():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 9.999) is False
    # exactly window_seconds old: no longer counts
    assert rl.allow("a", 10.0)


def test_sliding_not_fixed_window():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 6.0) is False
    # at t=10 the request from t=0 expires, leaving one slot
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0)
    assert rl.allow("a", 10.0) is False
    # at t=15 the request from t=5 expires
    assert rl.remaining("a", 15.0) == 1


def test_remaining_reflects_expiry():
    rl = RateLimiter(3, 4.0)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    rl.allow("a", 2.0)
    assert rl.remaining("a", 3.0) == 0
    assert rl.remaining("a", 4.0) == 1
    assert rl.remaining("a", 5.0) == 2
    assert rl.remaining("a", 6.0) == 3


# ----- retry_after -----------------------------------------------------------

def test_retry_after_zero_when_it_would_fit():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_single_expiry():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 2.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(7.0)  # expires at 12
    assert rl.retry_after("a", 12.0) == 0.0


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.allow("a", 10.0)


def test_retry_after_waits_for_enough_expiries_for_weighted_cost():
    rl = RateLimiter(4, 10.0)
    rl.allow("a", 0.0, 1)  # expires 10
    rl.allow("a", 2.0, 1)  # expires 12
    rl.allow("a", 4.0, 2)  # expires 14
    # used = 4; a cost-2 request needs 2 units freed
    # after t=10: used=3 -> 3+2>4 ; after t=12: used=2 -> 2+2<=4
    assert rl.retry_after("a", 5.0, 2) == pytest.approx(7.0)  # 12 - 5
    assert rl.retry_after("a", 5.0, 1) == pytest.approx(5.0)  # 10 - 5
    assert rl.retry_after("a", 5.0, 4) == pytest.approx(9.0)  # 14 - 5


def test_retry_after_matches_allow_outcome():
    rl = RateLimiter(3, 5.0)
    rl.allow("a", 0.0, 2)
    rl.allow("a", 1.0, 1)
    wait = rl.retry_after("a", 2.0, 2)
    assert wait > 0
    assert rl.allow("a", 2.0, 2) is False
    assert rl.allow("a", 2.0 + wait, 2) is True


def test_retry_after_is_nonnegative_and_consistent_at_boundary():
    rl = RateLimiter(1, 3.0)
    rl.allow("a", 0.0)
    wait = rl.retry_after("a", 1.0)
    assert wait >= 0.0
    assert rl.allow("a", 1.0 + wait) is True


# ----- time monotonicity -----------------------------------------------------

def test_time_going_backwards_raises_for_every_method():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 4.0)


def test_time_monotonic_is_global_across_clients():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 5.0)
    # a different client still cannot be asked about an earlier time
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)
    with pytest.raises(ValueError):
        rl.remaining("b", 1.0)


def test_equal_time_is_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("b", 5.0)
    assert rl.remaining("a", 5.0) == 0


def test_rejected_backwards_call_does_not_change_state():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    # the clock was not moved back; the window still ends at 15
    assert rl.allow("a", 14.9) is False
    assert rl.allow("a", 15.0)
