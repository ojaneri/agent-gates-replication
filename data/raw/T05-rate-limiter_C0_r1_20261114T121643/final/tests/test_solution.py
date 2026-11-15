import pytest

from solution import RateLimiter


# ----- construction ---------------------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", True, None])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, True, "1", None])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction():
    RateLimiter(1, 0.5)
    RateLimiter(10, 60)


# ----- cost validation --------------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, 1.0, True, "1"])
def test_invalid_cost_allow(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost=cost)


@pytest.mark.parametrize("cost", [0, 4, True])
def test_invalid_cost_retry_after(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost=cost)


def test_cost_bounds_inclusive():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3) is True
    assert rl.remaining("a", 0.0) == 0


# ----- basic allow / remaining --------------------------------------------------

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0) is False


def test_remaining_counts_down():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining("a", 0.0) == 3
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 2
    rl.allow("a", 1.0, cost=2)
    assert rl.remaining("a", 1.0) == 0


def test_remaining_does_not_record():
    rl = RateLimiter(2, 10.0)
    for _ in range(5):
        assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)


def test_weighted_cost():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.allow("a", 0.0, cost=2)
    assert rl.allow("a", 0.0, cost=1) is False


def test_cost_too_big_for_remaining_budget_is_rejected():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=4)
    assert rl.allow("a", 0.0, cost=2) is False
    assert rl.remaining("a", 0.0) == 1


# ----- rejected requests never use budget -------------------------------------

def test_rejected_requests_use_no_budget():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0)
    # many rejections at later times
    for t in (1.0, 2.0, 3.0):
        assert rl.allow("a", t) is False
    # both accepted requests (at t=0) expire at 10.0; budget is fully free again
    assert rl.allow("a", 10.0) is True
    assert rl.allow("a", 10.0) is True
    assert rl.allow("a", 10.0) is False


# ----- per-client isolation ---------------------------------------------------

def test_clients_are_independent():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0)
    assert rl.remaining("c", 0.0) == 1


# ----- sliding window boundary ---------------------------------------------------

def test_request_counts_strictly_before_window_end():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 9.999) is False
    assert rl.remaining("a", 9.999) == 0


def test_exactly_window_old_no_longer_counts():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True


def test_sliding_not_fixed_window():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 6.0) is False
    # only the t=0 request expires at t=10
    assert rl.allow("a", 10.0) is True
    assert rl.allow("a", 10.0) is False
    assert rl.allow("a", 15.0) is True


# ----- retry_after ---------------------------------------------------------------

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_when_full():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(5.0)
    assert rl.retry_after("a", 10.0) == 0.0


def test_retry_after_is_accurate():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 4.0)
    wait = rl.retry_after("a", 5.0)
    assert wait == pytest.approx(5.0)
    assert rl.allow("a", 5.0 + wait) is True


def test_retry_after_weighted_needs_multiple_expirations():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 0.0, cost=1)
    rl.allow("a", 2.0, cost=1)
    rl.allow("a", 4.0, cost=1)
    # need 2 units free: 0.0 and 2.0 both must expire -> at t=12
    assert rl.retry_after("a", 5.0, cost=2) == pytest.approx(7.0)
    # at 11.9 only the t=0 unit has expired; a cost-2 request still does not fit
    assert rl.allow("a", 11.9, cost=2) is False
    assert rl.allow("a", 12.0, cost=2) is True


def test_retry_after_does_not_record():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    before = rl.retry_after("a", 3.0)
    assert before == pytest.approx(7.0)
    assert rl.retry_after("a", 3.0) == pytest.approx(7.0)
    assert rl.remaining("a", 10.0) == 1


def test_retry_after_clients_independent():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("b", 1.0) == 0.0


# ----- time monotonicity ----------------------------------------------------------

def test_time_going_backwards_raises_for_allow():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)


def test_time_backwards_applies_across_clients():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)


def test_time_backwards_raises_for_remaining_and_retry_after():
    rl = RateLimiter(5, 10.0)
    rl.remaining("a", 5.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 1.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1.0)


def test_equal_time_is_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 3.0)
    assert rl.allow("b", 3.0)
    assert rl.allow("a", 3.0)
    assert rl.allow("a", 3.0) is False
