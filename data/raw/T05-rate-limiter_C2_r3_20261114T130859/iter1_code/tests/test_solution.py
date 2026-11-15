import pytest

from solution import RateLimiter


# --- constructor validation ---

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", None, True, False])
def test_invalid_limit_raises(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10)


@pytest.mark.parametrize("window", [0, 0.0, -1, -0.5, float("nan")])
def test_invalid_window_raises(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction_with_int_and_float_window():
    RateLimiter(1, 0.001)
    RateLimiter(5, 60)


# --- cost validation ---

@pytest.mark.parametrize("cost", [0, -1, 4, 1.0, "1", True, None])
def test_invalid_cost_on_allow_raises(cost):
    rl = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)


@pytest.mark.parametrize("cost", [0, 4, True])
def test_invalid_cost_on_retry_after_raises(cost):
    rl = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


def test_cost_one_is_default():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False


# --- basic accept / reject ---

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10)
    assert [rl.allow("a", 0.0) for _ in range(4)] == [True, True, True, False]


def test_allow_returns_real_bools():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False


def test_remaining_decreases_with_accepted_requests():
    rl = RateLimiter(5, 10)
    assert rl.remaining("a", 0.0) == 5
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 4
    rl.allow("a", 0.0, 3)
    assert rl.remaining("a", 0.0) == 1


def test_remaining_for_unknown_client_is_full_limit():
    rl = RateLimiter(7, 10)
    assert rl.remaining("nobody", 123.0) == 7


def test_weighted_cost_counts_units():
    rl = RateLimiter(5, 10)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.allow("a", 0.0, 3) is False
    assert rl.allow("a", 0.0, 2) is True
    assert rl.remaining("a", 0.0) == 0


def test_rejected_request_uses_no_budget():
    rl = RateLimiter(5, 10)
    assert rl.allow("a", 0.0, 4) is True
    assert rl.allow("a", 0.0, 2) is False
    assert rl.remaining("a", 0.0) == 1
    assert rl.allow("a", 0.0, 1) is True
    assert rl.remaining("a", 0.0) == 0


def test_rejected_request_is_not_recorded_for_expiry():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 1.0) is True
    assert rl.allow("a", 2.0) is False  # rejected at t=2, must not be stored
    # At t=10 only the request from t=0 has expired.
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True
    assert rl.remaining("a", 10.0) == 0


# --- clients are independent ---

def test_clients_have_separate_budgets():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0) is True
    assert rl.remaining("b", 0.0) == 0
    assert rl.remaining("c", 0.0) == 1


# --- sliding window expiry ---

def test_request_expires_exactly_at_window_boundary():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 9.999) is False
    assert rl.allow("a", 10.0) is True


def test_request_still_counts_just_before_window():
    rl = RateLimiter(1, 10)
    rl.allow("a", 5.0)
    assert rl.remaining("a", 14.999) == 0
    assert rl.remaining("a", 15.0) == 1


def test_sliding_not_fixed_window():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 6.0) is True
    assert rl.allow("a", 9.0) is False
    # Only the t=0 request has expired at t=10; the t=6 one still counts.
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True
    assert rl.remaining("a", 10.0) == 0


def test_expiry_frees_weighted_units():
    rl = RateLimiter(5, 10)
    rl.allow("a", 0.0, 4)
    rl.allow("a", 2.0, 1)
    assert rl.remaining("a", 9.0) == 0
    assert rl.remaining("a", 10.0) == 4
    assert rl.remaining("a", 12.0) == 5


def test_remaining_full_after_all_expired():
    rl = RateLimiter(3, 5)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    assert rl.remaining("a", 100.0) == 3


# --- remaining and retry_after record nothing ---

def test_remaining_records_nothing():
    rl = RateLimiter(2, 10)
    for _ in range(5):
        assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10)
    assert rl.retry_after("a", 0.0) == 0.0
    assert rl.retry_after("a", 0.0) == 0.0
    assert rl.allow("a", 0.0) is True


# --- retry_after ---

def test_retry_after_zero_when_capacity_available():
    rl = RateLimiter(2, 10)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == 0.0


def test_retry_after_zero_for_unknown_client():
    rl = RateLimiter(2, 10)
    assert rl.retry_after("x", 0.0) == 0.0


def test_retry_after_when_full():
    rl = RateLimiter(2, 10)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(5.0)
    assert rl.retry_after("a", 9.0) == pytest.approx(1.0)


def test_retry_after_matches_when_allow_succeeds():
    rl = RateLimiter(2, 10)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    wait = rl.retry_after("a", 5.0)
    assert rl.allow("a", 5.0 + wait - 1e-6) is False
    assert rl.allow("a", 5.0 + wait) is True


def test_retry_after_uses_oldest_needed_record():
    rl = RateLimiter(3, 10)
    rl.allow("a", 0.0)
    rl.allow("a", 2.0)
    rl.allow("a", 3.0)
    # Full. One unit frees when the t=0 request expires at t=10.
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)


def test_retry_after_weighted_cost_needs_multiple_expiries():
    rl = RateLimiter(4, 10)
    rl.allow("a", 0.0, 1)
    rl.allow("a", 1.0, 1)
    rl.allow("a", 2.0, 2)
    # Used 4 of 4. Cost 3 needs 3 units freed: t=0 gives 1, t=1 gives 2 total,
    # t=2 gives 4 total, so the wait is until t=12.
    assert rl.retry_after("a", 3.0, 3) == pytest.approx(9.0)


def test_retry_after_weighted_cost_partial_expiry_enough():
    rl = RateLimiter(4, 10)
    rl.allow("a", 0.0, 2)
    rl.allow("a", 1.0, 2)
    # Cost 2 needs 2 units: the t=0 record alone frees enough, at t=10.
    assert rl.retry_after("a", 5.0, 2) == pytest.approx(5.0)


def test_retry_after_cost_equal_to_limit_when_partially_used():
    rl = RateLimiter(3, 10)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    # used=2, cost=3, limit=3, so needed = 2. The t=0 record frees 1 and the
    # t=1 record frees 2 in total, so the wait ends at t=11 (9s after now=2).
    assert rl.retry_after("a", 2.0, 3) == pytest.approx(9.0)


def test_retry_after_is_nonnegative():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 9.999999) > 0.0
    assert rl.retry_after("a", 9.999999) < 1.0


# --- time monotonicity ---

def test_time_going_backwards_raises_on_allow():
    rl = RateLimiter(5, 10)
    rl.allow("a", 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 9.0)


def test_time_going_backwards_raises_for_other_client():
    rl = RateLimiter(5, 10)
    rl.allow("a", 10.0)
    with pytest.raises(ValueError):
        rl.allow("b", 9.5)


@pytest.mark.parametrize("method", ["remaining", "retry_after", "allow"])
def test_time_going_backwards_raises_on_every_method(method):
    rl = RateLimiter(5, 10)
    rl.allow("a", 10.0)
    with pytest.raises(ValueError):
        if method == "remaining":
            rl.remaining("a", 9.0)
        elif method == "retry_after":
            rl.retry_after("a", 9.0)
        else:
            rl.allow("a", 9.0)


def test_equal_times_are_fine():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is False
    assert rl.remaining("b", 5.0) == 2


def test_rejected_backwards_call_does_not_lower_latest_time():
    rl = RateLimiter(5, 10)
    rl.allow("a", 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 9.0)
    # Still 10 is the latest; 9.5 is still in the past.
    with pytest.raises(ValueError):
        rl.remaining("a", 9.5)
    assert rl.remaining("a", 10.0) == 4


def test_latest_time_tracked_across_methods():
    rl = RateLimiter(5, 10)
    rl.remaining("a", 20.0)
    with pytest.raises(ValueError):
        rl.allow("a", 19.0)


def test_invalid_cost_does_not_advance_time():
    rl = RateLimiter(2, 10)
    with pytest.raises(ValueError):
        rl.allow("a", 100.0, 0)
    # Time 100 was never accepted, so 50 is fine.
    assert rl.allow("a", 50.0) is True


def test_large_time_jump_clears_everything():
    rl = RateLimiter(2, 1)
    rl.allow("a", 0.0)
    rl.allow("a", 0.5)
    assert rl.remaining("a", 1000.0) == 2
