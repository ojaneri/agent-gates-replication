import pytest

from solution import RateLimiter


# ----- constructor validation -----

@pytest.mark.parametrize("limit", [0, -1, True, False, 1.5, "3", None])
def test_bad_limit_rejected(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0])
def test_bad_window_rejected(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction():
    RateLimiter(1, 0.5)
    RateLimiter(10, 60)


# ----- cost validation -----

@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0])
def test_bad_cost_rejected(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_equal_to_limit_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


# ----- basic accept / reject -----

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert [rl.allow("a", 0.0) for _ in range(4)] == [True, True, True, False]


def test_default_cost_is_one():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 1


def test_weighted_cost():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, 3)
    assert not rl.allow("a", 0.0, 3)  # 3 + 3 > 5
    assert rl.allow("a", 0.0, 2)      # 3 + 2 == 5
    assert rl.remaining("a", 0.0) == 0


# ----- per-client isolation -----

def test_clients_are_independent():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.0)
    assert rl.allow("b", 0.0)
    assert rl.remaining("c", 0.0) == 1


# ----- window expiry -----

def test_request_exactly_window_old_no_longer_counts():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 9.999)
    assert rl.allow("a", 10.0)


def test_partial_expiry_frees_only_expired_units():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 1)
    assert rl.allow("a", 5.0, 2)
    assert rl.remaining("a", 9.0) == 0
    assert rl.remaining("a", 10.0) == 1  # cost-1 request expired, cost-2 still live
    assert rl.remaining("a", 15.0) == 3


# ----- rejected requests use no budget -----

def test_rejected_request_records_nothing():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0, 2)
    assert not rl.allow("a", 1.0, 1)
    assert not rl.allow("a", 2.0, 1)
    # Only the first request occupies budget; it expires at 10.0.
    assert rl.remaining("a", 9.0) == 0
    assert rl.allow("a", 10.0, 2)


# ----- remaining and retry_after are read-only -----

def test_remaining_records_nothing():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    for _ in range(5):
        assert rl.remaining("a", 1.0) == 1
    assert rl.allow("a", 1.0)
    assert rl.remaining("a", 1.0) == 0


def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    assert rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.remaining("a", 4.0) == 0


def test_retry_after_single_request():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 2.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(7.0)
    assert rl.retry_after("a", 12.0) == 0.0


def test_retry_after_accounts_for_cost():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, 2)  # expires at 10
    assert rl.allow("a", 3.0, 3)  # expires at 13; budget now full
    # Need 3 units: only the first (cost 2) is not enough, need the second too.
    assert rl.retry_after("a", 4.0, 3) == pytest.approx(9.0)
    # Need 2 units: the first record alone frees enough, at t=10.
    assert rl.retry_after("a", 4.0, 2) == pytest.approx(6.0)


def test_retry_after_cost_one_with_mixed_costs():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 1)
    assert rl.allow("a", 1.0, 2)
    # Full. Cost 1 fits once the t=0 record expires at 10.
    assert rl.retry_after("a", 2.0, 1) == pytest.approx(8.0)


# ----- time monotonicity -----

def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 5.0)
    assert not rl.allow("a", 5.0)


def test_time_going_backwards_raises_for_any_method():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 4.0)


def test_backwards_check_applies_across_clients():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 1.0)


def test_time_going_backwards_does_not_change_state():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    assert rl.remaining("a", 5.0) == 0
    assert rl.allow("a", 15.0)
