import pytest

from solution import RateLimiter


# ----- construction -------------------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", None, True, False])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("window", [0, 0.0, -1, -0.5, float("nan"), True, "1", None])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        RateLimiter(2, window)


def test_valid_construction_with_int_window():
    rl = RateLimiter(2, 10)
    assert rl.allow("a", 0)


# ----- basic allow / remaining -------------------------------------------

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 1.0)
    assert rl.allow("a", 2.0)
    assert rl.allow("a", 3.0) is False


def test_remaining_counts_down():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining("a", 0.0) == 3
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 2
    rl.allow("a", 0.0, cost=2)
    assert rl.remaining("a", 0.0) == 0


def test_remaining_records_nothing():
    rl = RateLimiter(1, 10.0)
    for t in range(5):
        assert rl.remaining("a", float(t)) == 1
    assert rl.allow("a", 5.0)
    assert rl.remaining("a", 5.0) == 0


def test_remaining_unknown_client_is_full():
    rl = RateLimiter(4, 1.0)
    assert rl.remaining("nobody", 0.0) == 4


# ----- window expiry -----------------------------------------------------

def test_request_exactly_window_old_no_longer_counts():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 9.999) is False
    assert rl.allow("a", 10.0) is True


def test_expiry_frees_budget_gradually():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("a", 6.0) is False
    assert rl.remaining("a", 9.0) == 0
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0)
    assert rl.remaining("a", 15.0) == 1
    assert rl.remaining("a", 20.0) == 2


def test_expired_entries_are_removed_entirely():
    rl = RateLimiter(1, 1.0)
    assert rl.allow("a", 0.0)
    assert rl.remaining("a", 100.0) == 1
    assert "a" not in rl._records


def test_cost_weighted_expiry():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.allow("a", 4.0, cost=2)
    assert rl.allow("a", 5.0, cost=1) is False
    assert rl.remaining("a", 5.0) == 0


# ----- cost validation ---------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0, "1", None])
def test_invalid_cost_allow(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost=cost)


@pytest.mark.parametrize("cost", [0, 4, True])
def test_invalid_cost_retry_after(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost=cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, cost=3)
    assert rl.remaining("a", 0.0) == 0


# ----- client isolation --------------------------------------------------

def test_clients_are_independent():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("b", 0.0)
    assert rl.allow("a", 0.0) is False
    assert rl.remaining("b", 0.0) == 0
    assert rl.remaining("c", 0.0) == 1


# ----- rejected requests -------------------------------------------------

def test_rejected_request_uses_no_budget():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 1.0, cost=2) is False
    assert rl.remaining("a", 1.0) == 1
    assert rl.allow("a", 1.0)


# ----- retry_after -------------------------------------------------------

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_single_entry():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 3.0) == pytest.approx(7.0)


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.allow("a", 10.0)


def test_retry_after_waits_for_enough_expirations():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 2.0)
    rl.allow("a", 4.0)
    # Need 2 units; expiring at 10 frees only 1, expiring at 12 frees 2.
    assert rl.retry_after("a", 5.0, cost=2) == pytest.approx(7.0)
    assert rl.retry_after("a", 5.0, cost=1) == pytest.approx(5.0)
    # Need all 3 units; only after the third entry expires at 14 do they fit.
    assert rl.retry_after("a", 5.0, cost=3) == pytest.approx(9.0)


def test_retry_after_matches_allow_at_returned_time():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 0.0, cost=2)
    rl.allow("a", 1.0)
    wait = rl.retry_after("a", 2.0, cost=2)
    assert wait == pytest.approx(8.0)
    assert rl.allow("a", 2.0, cost=2) is False
    assert rl.allow("a", 2.0 + wait, cost=2) is True


def test_retry_after_multi_entries_same_expiry_chain():
    rl = RateLimiter(4, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    rl.allow("a", 2.0, cost=2)
    # Frees 1 at t=10, 2 at t=11 (not enough for cost 3 until the 4-unit entry at t=12 expires).
    assert rl.retry_after("a", 3.0, cost=3) == pytest.approx(9.0)


# ----- time monotonicity -------------------------------------------------

def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0)
    assert rl.allow("b", 5.0)
    assert rl.remaining("a", 5.0) == 1


def test_time_going_backwards_raises_for_any_method():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 1.0)


def test_rejected_backwards_call_does_not_lower_clock():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    assert rl.allow("a", 5.0)


@pytest.mark.parametrize("now", [True, None, "1", float("nan")])
def test_invalid_now(now):
    rl = RateLimiter(2, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", now)
    with pytest.raises(ValueError):
        rl.remaining("a", now)
    with pytest.raises(ValueError):
        rl.retry_after("a", now)


def test_integer_now_accepted():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0)
    assert rl.allow("a", 10) is True
