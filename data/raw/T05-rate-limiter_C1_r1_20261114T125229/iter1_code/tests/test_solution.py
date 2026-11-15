import pytest

from solution import RateLimiter


# --- constructor validation (rule 1) ---

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", None, True, False])
def test_invalid_limit_raises(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, "10", None, True, float("nan")])
def test_invalid_window_raises(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction_accepts_int_window():
    rl = RateLimiter(1, 5)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 1.0)


# --- cost validation (rule 2) ---

@pytest.mark.parametrize("cost", [0, -1, 4, 1.0, "1", None, True])
def test_invalid_cost_allow_raises(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost=cost)


@pytest.mark.parametrize("cost", [0, 4, True, 2.0])
def test_invalid_cost_retry_after_raises(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost=cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.remaining("a", 0.0) == 0


# --- basic allow / reject (rule 5) ---

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.0)


def test_rejected_requests_do_not_use_budget():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=2)
    assert not rl.allow("a", 1.0, cost=2)  # would need 4 > 3
    assert rl.remaining("a", 1.0) == 1
    assert rl.allow("a", 1.0, cost=1)
    assert rl.remaining("a", 1.0) == 0


def test_weighted_costs_sum_against_limit():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=2)
    assert rl.allow("a", 0.0, cost=2)
    assert not rl.allow("a", 0.0, cost=2)
    assert rl.allow("a", 0.0, cost=1)
    assert not rl.allow("a", 0.0, cost=1)


# --- per-client isolation (rule 3) ---

def test_clients_have_independent_budgets():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.0)
    assert rl.allow("b", 0.0)
    assert rl.remaining("b", 0.0) == 0
    assert rl.remaining("c", 0.0) == 1


# --- window expiry (rule 4) ---

def test_request_expires_exactly_at_window_boundary():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 9.999)
    assert rl.allow("a", 10.0)


def test_partial_expiry_frees_only_old_requests():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 5.0)
    assert rl.remaining("a", 9.0) == 0
    assert rl.remaining("a", 10.0) == 1
    assert rl.remaining("a", 15.0) == 2


def test_expired_request_removed_for_unknown_client_is_safe():
    rl = RateLimiter(2, 1.0)
    assert rl.remaining("ghost", 0.0) == 2
    assert rl.retry_after("ghost", 0.0) == 0.0


# --- remaining (rule 6) ---

def test_remaining_does_not_record():
    rl = RateLimiter(2, 10.0)
    for _ in range(5):
        assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.0)


def test_remaining_never_negative_or_below_zero_units_used():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.remaining("a", 0.0) == 0


# --- retry_after (rule 7) ---

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    assert rl.retry_after("a", 0.0, cost=2) == 0.0


def test_retry_after_when_full():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 4.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.retry_after("a", 9.0) == pytest.approx(1.0)


def test_retry_after_is_exact_moment_request_becomes_acceptable():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    wait = rl.retry_after("a", 2.0)
    assert wait == pytest.approx(8.0)
    assert not rl.allow("a", 2.0 + wait - 1e-6)
    assert rl.allow("a", 2.0 + wait)


def test_retry_after_needs_multiple_expiries_for_large_cost():
    rl = RateLimiter(4, 10.0)
    assert rl.allow("a", 0.0)  # t=0
    assert rl.allow("a", 1.0)  # t=1
    assert rl.allow("a", 2.0)  # t=2
    assert rl.allow("a", 3.0)  # t=3
    # cost 3 needs 3 units freed: expiries at 10, 11, 12 -> third one at t=12
    assert rl.retry_after("a", 3.0, cost=3) == pytest.approx(9.0)
    # cost 1 only needs the first expiry at t=10
    assert rl.retry_after("a", 3.0, cost=1) == pytest.approx(7.0)


def test_retry_after_with_weighted_entries():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=2)  # expires at 10
    assert rl.allow("a", 1.0, cost=1)  # expires at 11
    # cost 2 requires the first entry to expire (frees 2 units)
    assert rl.retry_after("a", 1.0, cost=2) == pytest.approx(9.0)
    # cost 3 requires both to expire
    assert rl.retry_after("a", 1.0, cost=3) == pytest.approx(10.0)


def test_retry_after_does_not_record():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    for _ in range(3):
        assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.allow("a", 10.0)


# --- time monotonicity (rule 8) ---

def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("b", 5.0)
    assert rl.remaining("a", 5.0) == 1
    assert rl.retry_after("a", 5.0, cost=2) == pytest.approx(10.0)


def test_time_going_backwards_raises_for_allow():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)


def test_time_going_backwards_raises_for_remaining():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.9)


def test_time_going_backwards_raises_for_retry_after():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1.0)


def test_monotonic_check_is_global_across_clients():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.0)
    # the rejected call must not have moved the clock back
    assert rl.allow("b", 5.0)


def test_non_numeric_time_raises():
    rl = RateLimiter(5, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", "now")
    with pytest.raises(ValueError):
        rl.remaining("a", True)
    with pytest.raises(ValueError):
        rl.retry_after("a", None)


def test_invalid_cost_does_not_advance_clock():
    rl = RateLimiter(2, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 100.0, cost=0)
    # clock was not advanced by the failed call, so an earlier time is still ok
    assert rl.allow("a", 1.0)
