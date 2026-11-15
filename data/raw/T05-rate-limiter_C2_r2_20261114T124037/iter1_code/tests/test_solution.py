import pytest

from solution import RateLimiter


# --- construction ---------------------------------------------------------

def test_valid_construction_starts_full():
    rl = RateLimiter(3, 1.5)
    assert rl.remaining("a", 0.0) == 3


def test_limit_of_one_is_allowed():
    rl = RateLimiter(1, 1)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.5)


@pytest.mark.parametrize("limit", [0, -1, True, False, 1.0, "3", None])
def test_bad_limit_raises(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, float("nan")])
def test_bad_window_raises(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


# --- allow and budgets ----------------------------------------------------

def test_allow_until_budget_is_full():
    rl = RateLimiter(3, 10)
    assert [rl.allow("a", 0.0) for _ in range(4)] == [True, True, True, False]


def test_clients_have_independent_budgets():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0)
    assert rl.allow("b", 0)
    assert not rl.allow("a", 0)
    assert not rl.allow("b", 0)


def test_window_boundary_exact_expiry():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 9.999)
    assert rl.allow("a", 10.0)


def test_expiry_frees_budget_one_request_at_a_time():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0)
    assert rl.allow("a", 5)
    assert not rl.allow("a", 9)
    assert rl.allow("a", 10)  # request at 0 expired, request at 5 still counts
    assert not rl.allow("a", 10)
    assert rl.allow("a", 15)


def test_cost_uses_multiple_units():
    rl = RateLimiter(5, 10)
    assert rl.allow("a", 0, cost=3)
    assert not rl.allow("a", 0, cost=3)
    assert rl.allow("a", 0, cost=2)
    assert rl.remaining("a", 0) == 0


def test_cost_equal_to_limit():
    rl = RateLimiter(4, 10)
    assert rl.allow("a", 0, cost=4)
    assert not rl.allow("a", 1)
    assert rl.allow("a", 10, cost=4)


def test_rejected_request_does_not_use_budget():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0, cost=2)
    assert not rl.allow("a", 1, cost=1)
    # If the rejected request had been recorded, it would still block here.
    assert rl.allow("a", 10, cost=2)


def test_rejected_large_cost_leaves_remaining_unchanged():
    rl = RateLimiter(3, 10)
    assert rl.allow("a", 0, cost=1)
    assert not rl.allow("a", 0, cost=3)
    assert rl.remaining("a", 0) == 2


# --- remaining ------------------------------------------------------------

def test_remaining_reports_units_and_records_nothing():
    rl = RateLimiter(3, 10)
    rl.allow("a", 0)
    assert rl.remaining("a", 1) == 2
    assert rl.remaining("a", 1) == 2
    assert rl.remaining("a", 10) == 3


def test_remaining_for_unknown_client_is_limit():
    rl = RateLimiter(7, 10)
    assert rl.remaining("nobody", 3.0) == 7
    assert rl.allow("nobody", 3.0)
    assert rl.remaining("nobody", 3.0) == 6


def test_remaining_counts_costs():
    rl = RateLimiter(10, 10)
    rl.allow("a", 0, cost=4)
    rl.allow("a", 1, cost=3)
    assert rl.remaining("a", 2) == 3


# --- retry_after ----------------------------------------------------------

def test_retry_after_zero_when_request_fits():
    rl = RateLimiter(2, 10)
    assert rl.retry_after("a", 0) == 0.0
    rl.allow("a", 0)
    assert rl.retry_after("a", 1) == 0.0


def test_retry_after_single_expiry():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0)
    assert rl.retry_after("a", 3) == pytest.approx(7.0)
    assert rl.retry_after("a", 9.5) == pytest.approx(0.5)
    assert rl.retry_after("a", 10) == 0.0


def test_retry_after_returns_float():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0)
    assert isinstance(rl.retry_after("a", 4), float)


def test_retry_after_waits_for_enough_expiries():
    rl = RateLimiter(3, 10)
    rl.allow("a", 0, cost=1)
    rl.allow("a", 2, cost=1)
    rl.allow("a", 4, cost=1)
    # cost 1: the request at 0 expires at 10
    assert rl.retry_after("a", 5, cost=1) == pytest.approx(5.0)
    # cost 2: the requests at 0 and 2 must both expire; 2 expires at 12
    assert rl.retry_after("a", 5, cost=2) == pytest.approx(7.0)


def test_retry_after_uses_costs_when_freeing():
    rl = RateLimiter(4, 10)
    rl.allow("a", 0, cost=3)
    rl.allow("a", 1, cost=1)
    # need 2 units free: expiry of the cost-3 request (at 10) frees enough
    assert rl.retry_after("a", 2, cost=2) == pytest.approx(8.0)


def test_retry_after_matches_allow():
    rl = RateLimiter(2, 10)
    rl.allow("a", 0)
    rl.allow("a", 4)
    wait = rl.retry_after("a", 5)
    assert wait == pytest.approx(5.0)
    assert not rl.allow("a", 5 + wait - 0.01)
    assert rl.allow("a", 5 + wait)


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0)
    rl.retry_after("a", 5)
    assert rl.allow("a", 10)


def test_retry_after_is_per_client():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0)
    assert rl.retry_after("b", 1) == 0.0


# --- cost validation ------------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, True, False, 1.0, "1", None])
def test_bad_cost_raises_everywhere(cost):
    rl = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        rl.allow("a", 0, cost=cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0, cost=cost)


def test_bad_cost_records_nothing():
    rl = RateLimiter(1, 10)
    with pytest.raises(ValueError):
        rl.allow("a", 0, cost=2)
    assert rl.allow("a", 0)


# --- time monotonicity ----------------------------------------------------

def test_time_going_backwards_raises_for_every_method():
    rl = RateLimiter(2, 10)
    rl.allow("a", 5)
    with pytest.raises(ValueError):
        rl.allow("a", 4)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)
    with pytest.raises(ValueError):
        rl.remaining("b", 4.9)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1)


def test_equal_time_is_fine():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 5)
    assert rl.allow("a", 5)
    assert rl.remaining("a", 5) == 0
    # both requests were made at 5, so both expire at 15
    assert rl.retry_after("a", 5) == pytest.approx(10.0)


def test_rejected_call_still_advances_seen_time():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 5)
    assert not rl.allow("a", 6)
    with pytest.raises(ValueError):
        rl.allow("b", 5.5)


def test_time_check_is_global_across_clients():
    rl = RateLimiter(5, 10)
    rl.allow("a", 100)
    with pytest.raises(ValueError):
        rl.allow("fresh-client", 99)
