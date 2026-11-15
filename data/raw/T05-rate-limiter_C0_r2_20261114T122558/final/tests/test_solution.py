import pytest

from solution import RateLimiter


# ----- construction ------------------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, True, False, 1.0, "3", None])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, -0.5])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction():
    RateLimiter(1, 0.001)
    RateLimiter(5, 60)


# ----- allow / cost -------------------------------------------------------

def test_basic_limit():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 1.0)
    assert rl.allow("a", 2.0)
    assert not rl.allow("a", 3.0)


def test_clients_are_independent():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 1.0)
    assert rl.allow("b", 1.0)


def test_request_expires_at_exactly_window():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 9.999)
    assert rl.allow("a", 10.0)


def test_cost_consumes_multiple_units():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.allow("a", 0.0, cost=2)
    assert not rl.allow("a", 0.0, cost=1)


def test_expensive_request_rejected_when_not_fitting():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=4)
    assert not rl.allow("a", 1.0, cost=2)
    # the rejected request used nothing
    assert rl.remaining("a", 1.0) == 1
    assert rl.allow("a", 1.0, cost=1)


def test_rejected_requests_do_not_use_budget():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    for t in (1.0, 2.0, 3.0):
        assert not rl.allow("a", t)
    # Only the two accepted requests (at t=0) count; they expire at t=10.
    assert rl.allow("a", 10.0)
    assert rl.allow("a", 10.0)
    assert not rl.allow("a", 10.0)


@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0, "1"])
def test_invalid_cost(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost=cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost=cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert not rl.allow("a", 0.0)


# ----- remaining ------------------------------------------------------------

def test_remaining_tracks_usage_and_expiry():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining("a", 0.0) == 3
    rl.allow("a", 0.0, cost=2)
    assert rl.remaining("a", 1.0) == 1
    assert rl.remaining("a", 9.0) == 1
    assert rl.remaining("a", 10.0) == 3


def test_remaining_records_nothing():
    rl = RateLimiter(1, 10.0)
    assert rl.remaining("a", 0.0) == 1
    assert rl.remaining("a", 0.0) == 1
    assert rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 0


def test_remaining_unknown_client_is_full():
    rl = RateLimiter(4, 10.0)
    assert rl.remaining("nobody", 5.0) == 4


# ----- retry_after ----------------------------------------------------------

def test_retry_after_zero_when_allowed():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == 0.0


def test_retry_after_until_oldest_expires():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(5.0)
    assert rl.retry_after("a", 9.0) == pytest.approx(1.0)


def test_retry_after_is_accurate():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    wait = rl.retry_after("a", 5.0)
    assert not rl.allow("a", 5.0)
    assert rl.allow("a", 5.0 + wait)


def test_retry_after_for_large_cost_needs_multiple_expiries():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 0.0, cost=1)   # expires at 10
    rl.allow("a", 2.0, cost=2)   # expires at 12
    rl.allow("a", 4.0, cost=2)   # expires at 14
    # in use = 5; cost 3 needs 3 units freed: first expiry frees 1 (not enough),
    # second frees 2 more -> 3 freed at t=12.
    assert rl.retry_after("a", 5.0, cost=3) == pytest.approx(7.0)
    assert rl.retry_after("a", 5.0, cost=1) == pytest.approx(5.0)
    assert rl.retry_after("a", 5.0, cost=5) == pytest.approx(9.0)


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.remaining("a", 10.0) == 1


def test_retry_after_is_per_client():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("b", 1.0) == 0.0


# ----- time monotonicity -----------------------------------------------------

def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 5.0)
    assert rl.remaining("b", 5.0) == 2


def test_time_going_backwards_raises_for_allow():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)


def test_time_going_backwards_raises_across_clients():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)


@pytest.mark.parametrize("method", ["remaining", "retry_after", "allow"])
def test_time_going_backwards_raises_for_every_method(method):
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        getattr(rl, method)("a", 1.0)


def test_rejected_backwards_call_does_not_change_state():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    assert rl.remaining("a", 5.0) == 0
    assert rl.remaining("a", 14.9) == 0
    assert rl.remaining("a", 15.0) == 1
