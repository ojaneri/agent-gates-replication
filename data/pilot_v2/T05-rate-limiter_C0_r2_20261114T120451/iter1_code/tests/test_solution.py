import pytest

from solution import RateLimiter


# ----- constructor validation ----------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 1.5, "3", None, True, False])
def test_invalid_limit_raises(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, float("nan")])
def test_invalid_window_raises(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction():
    RateLimiter(1, 0.5)
    RateLimiter(10, 60)


# ----- cost validation -------------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0])
def test_invalid_cost_raises(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost=cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost=cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3) is True
    assert rl.remaining("a", 0.0) == 0


# ----- basic allow / remaining ----------------------------------------------

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert [rl.allow("a", 0.0) for _ in range(4)] == [True, True, True, False]


def test_remaining_counts_down():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining("a", 0.0) == 3
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 2
    rl.allow("a", 0.0, cost=2)
    assert rl.remaining("a", 0.0) == 0


def test_remaining_records_nothing():
    rl = RateLimiter(2, 10.0)
    for _ in range(5):
        assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False


# ----- clients are independent ----------------------------------------------

def test_clients_have_independent_budgets():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0) is True
    assert rl.remaining("c", 0.0) == 1


# ----- window expiry ---------------------------------------------------------

def test_request_expires_strictly_before_window_end():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 9.999) is False


def test_request_exactly_window_old_no_longer_counts():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True


def test_partial_expiry_frees_only_old_requests():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 9.0) is False
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True
    assert rl.allow("a", 10.0) is False


# ----- rejected requests use no budget --------------------------------------

def test_rejected_request_records_nothing():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=2) is True
    assert rl.allow("a", 1.0, cost=2) is False  # 2+2 > 3, rejected
    assert rl.remaining("a", 1.0) == 1
    assert rl.allow("a", 1.0, cost=1) is True


# ----- weighted costs ---------------------------------------------------------

def test_weighted_costs_respect_limit():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=3) is True
    assert rl.allow("a", 0.0, cost=3) is False
    assert rl.allow("a", 0.0, cost=2) is True
    assert rl.remaining("a", 0.0) == 0


def test_weighted_request_expires_as_a_unit():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=4) is True
    assert rl.allow("a", 5.0, cost=2) is False
    assert rl.allow("a", 10.0, cost=2) is True


# ----- retry_after -----------------------------------------------------------

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_when_full():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 2.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(7.0)
    assert rl.retry_after("a", 12.0) == pytest.approx(0.0)


def test_retry_after_matches_actual_acceptance():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 3.0)
    wait = rl.retry_after("a", 4.0)
    assert wait == pytest.approx(6.0)  # oldest (t=0) expires at t=10
    assert rl.allow("a", 4.0 + wait - 1e-6) is False
    assert rl.allow("a", 4.0 + wait) is True


def test_retry_after_with_weighted_cost_needs_multiple_expiries():
    rl = RateLimiter(4, 10.0)
    rl.allow("a", 0.0, cost=1)
    rl.allow("a", 1.0, cost=1)
    rl.allow("a", 2.0, cost=2)
    # 4 in use; cost 3 needs 3 units free -> expire t=0 (frees 1) and t=1 (frees 1)
    # -> 2 free, not enough; need t=2 too, which frees 2 -> 4 free.
    # Expiry of t=2 is at 12.0; only then does cost 3 fit.
    assert rl.retry_after("a", 3.0, cost=3) == pytest.approx(9.0)
    # Cost 2 fits once the t=0 and t=1 entries expire (at t=11)
    assert rl.retry_after("a", 3.0, cost=2) == pytest.approx(8.0)


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    for _ in range(3):
        assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.remaining("a", 10.0) == 1


# ----- time monotonicity -----------------------------------------------------

def test_backwards_time_raises_for_allow():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)


def test_backwards_time_raises_across_clients():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)


def test_backwards_time_raises_for_remaining_and_retry_after():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 1.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1.0)


def test_equal_time_is_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is False
