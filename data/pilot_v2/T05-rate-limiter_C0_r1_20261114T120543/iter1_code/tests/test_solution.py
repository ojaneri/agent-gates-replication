import pytest

from solution import RateLimiter


# ----- construction -----

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", None, True, False])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1, -0.5])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        RateLimiter(1, window)


def test_valid_construction():
    RateLimiter(1, 0.5)
    RateLimiter(10, 60)


# ----- cost validation -----

@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0, "1"])
def test_invalid_cost_allow(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)


@pytest.mark.parametrize("cost", [0, 4, True])
def test_invalid_cost_retry_after(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_up_to_limit_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


# ----- basic allow / remaining -----

def test_allow_until_limit_then_reject():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 1.0) is True
    assert rl.allow("a", 2.0) is False


def test_remaining_tracks_usage():
    rl = RateLimiter(5, 10.0)
    assert rl.remaining("a", 0.0) == 5
    rl.allow("a", 0.0, 2)
    assert rl.remaining("a", 0.0) == 3
    rl.allow("a", 1.0)
    assert rl.remaining("a", 1.0) == 2


def test_remaining_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.remaining("a", 0.0)
    rl.remaining("a", 0.0)
    assert rl.allow("a", 0.0) is True
    assert rl.remaining("a", 0.0) == 0


def test_rejected_requests_use_no_budget():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 2) is True
    assert rl.allow("a", 0.0, 2) is False  # would need 4 > 3
    assert rl.remaining("a", 0.0) == 1
    assert rl.allow("a", 0.0, 1) is True
    assert rl.remaining("a", 0.0) == 0


def test_weighted_cost_fits_exactly():
    rl = RateLimiter(4, 10.0)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.allow("a", 0.0, 2) is False
    assert rl.allow("a", 0.0, 1) is True


# ----- window expiry -----

def test_request_expires_exactly_at_window():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 9.999) is False
    # Exactly window_seconds old no longer counts.
    assert rl.allow("a", 10.0) is True


def test_remaining_restores_after_expiry():
    rl = RateLimiter(3, 5.0)
    rl.allow("a", 0.0, 2)
    rl.allow("a", 2.0, 1)
    assert rl.remaining("a", 4.0) == 0
    assert rl.remaining("a", 5.0) == 2  # cost-2 request expired, cost-1 still active
    assert rl.remaining("a", 6.9) == 2
    assert rl.remaining("a", 7.0) == 3  # cost-1 request expired too


def test_partial_expiry_frees_only_old_requests():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 9.0) is False
    assert rl.allow("a", 10.0) is True   # t=0 expired
    assert rl.allow("a", 14.0) is False  # t=5 still active, t=10 active
    assert rl.allow("a", 15.0) is True   # t=5 expired


# ----- client isolation -----

def test_clients_are_independent():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0) is True
    assert rl.remaining("c", 0.0) == 1


def test_rejection_for_one_client_does_not_affect_other():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0, 2)
    assert rl.allow("a", 1.0) is False
    assert rl.remaining("b", 1.0) == 2


# ----- retry_after -----

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == 0.0


def test_retry_after_single_entry():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 3.0) == pytest.approx(7.0)
    assert rl.retry_after("a", 10.0) == 0.0


def test_retry_after_waits_for_enough_expiries():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 0.0)      # expires at 10
    rl.allow("a", 2.0)      # expires at 12
    rl.allow("a", 4.0)      # expires at 14
    # Cost 2 needs two entries gone: the one at t=0 and t=2 -> at 12.
    assert rl.retry_after("a", 5.0, 2) == pytest.approx(7.0)
    # Cost 1 needs only the t=0 entry -> at 10.
    assert rl.retry_after("a", 5.0, 1) == pytest.approx(5.0)
    # Cost 3 needs all three -> at 14.
    assert rl.retry_after("a", 5.0, 3) == pytest.approx(9.0)


def test_retry_after_is_consistent_with_allow():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0, 2)
    wait = rl.retry_after("a", 4.0, 2)
    assert wait == pytest.approx(6.0)
    assert rl.allow("a", 4.0 + wait - 1e-9, 2) is False
    assert rl.allow("a", 4.0 + wait, 2) is True


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    rl.retry_after("a", 5.0)
    rl.retry_after("a", 5.0)
    assert rl.allow("a", 10.0) is True


def test_retry_after_unknown_client():
    rl = RateLimiter(1, 10.0)
    assert rl.retry_after("nobody", 0.0) == 0.0


# ----- time monotonicity -----

def test_backwards_time_raises_in_allow():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)


def test_backwards_time_raises_across_clients():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)


def test_backwards_time_raises_in_remaining_and_retry_after():
    rl = RateLimiter(5, 10.0)
    rl.remaining("a", 5.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 1.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1.0)


def test_equal_time_is_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 3.0) is True
    assert rl.allow("a", 3.0) is True
    assert rl.allow("a", 3.0) is False
