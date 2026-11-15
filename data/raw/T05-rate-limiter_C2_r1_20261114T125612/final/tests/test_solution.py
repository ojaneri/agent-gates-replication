import pytest

from solution import RateLimiter


# --- constructor validation ---

@pytest.mark.parametrize("limit", [0, -1, 1.5, "3", None, True, False])
def test_invalid_limit_rejected(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0, float("nan"), True, "5", None])
def test_invalid_window_rejected(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_valid_construction_with_int_window():
    rl = RateLimiter(1, 5)
    assert rl.allow("a", 0.0) is True


# --- cost validation ---

@pytest.mark.parametrize("cost", [0, -1, 4, 1.0, True, "1", None])
def test_invalid_cost_rejected_by_allow(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)


@pytest.mark.parametrize("cost", [0, 4, True])
def test_invalid_cost_rejected_by_retry_after(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


def test_invalid_cost_does_not_advance_time():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 100.0, 0)
    # time was not advanced by the rejected call, so 5.0 is still valid
    assert rl.remaining("a", 5.0) == 2


# --- basic allow / remaining ---

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert [rl.allow("a", 0.0) for _ in range(4)] == [True, True, True, False]


def test_remaining_decreases_with_accepted_requests():
    rl = RateLimiter(5, 10.0)
    assert rl.remaining("a", 0.0) == 5
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.0) == 4
    rl.allow("a", 1.0, 2)
    assert rl.remaining("a", 1.0) == 2


def test_remaining_never_negative_and_never_below_zero():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0, 2)
    assert rl.remaining("a", 0.0) == 0


def test_remaining_records_nothing():
    rl = RateLimiter(2, 10.0)
    for _ in range(5):
        assert rl.remaining("a", 0.0) == 2
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False


def test_weighted_cost_counts_units():
    rl = RateLimiter(10, 10.0)
    assert rl.allow("a", 0.0, 7) is True
    assert rl.allow("a", 0.0, 4) is False
    assert rl.allow("a", 0.0, 3) is True
    assert rl.remaining("a", 0.0) == 0


# --- clients are independent ---

def test_clients_have_separate_budgets():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 0.0) is False
    assert rl.allow("b", 0.0) is True
    assert rl.remaining("c", 0.0) == 1


def test_unknown_client_remaining_is_full_limit():
    rl = RateLimiter(4, 1.0)
    assert rl.remaining("nobody", 0.0) == 4


# --- sliding window expiry ---

def test_request_expires_exactly_at_window_boundary():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 9.999) is False
    # exactly window_seconds old: no longer counts
    assert rl.allow("a", 10.0) is True


def test_request_still_counts_just_before_expiry():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    assert rl.remaining("a", 9.5) == 0


def test_partial_expiry_frees_only_old_requests():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 6.0) is False
    # at t=10 the request from t=0 has expired, the one from t=5 has not
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True
    assert rl.remaining("a", 10.0) == 0


def test_expiry_of_weighted_request_frees_its_full_cost():
    rl = RateLimiter(5, 4.0)
    assert rl.allow("a", 0.0, 4) is True
    assert rl.remaining("a", 3.0) == 1
    assert rl.remaining("a", 4.0) == 5


def test_rejected_requests_never_use_budget():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    assert rl.allow("a", 2.0) is False
    assert rl.allow("a", 3.0) is False
    # only the t=0 and t=1 requests were recorded; they expire at 10 and 11
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0) is True
    assert rl.remaining("a", 10.0) == 0


def test_rejected_request_at_later_time_does_not_block_window():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("a", 5.0) is False
    # if the rejection had been recorded, t=5 would block until t=15
    assert rl.allow("a", 10.0) is True


# --- retry_after ---

def test_retry_after_zero_when_request_fits():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 1.0) == 0.0


def test_retry_after_when_full():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 2.0)
    assert rl.retry_after("a", 5.0) == pytest.approx(7.0)


def test_retry_after_is_zero_at_exact_expiry():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 2.0)
    assert rl.retry_after("a", 12.0) == 0.0


def test_retry_after_matches_when_allow_succeeds():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    wait = rl.retry_after("a", 3.0)
    assert wait == pytest.approx(7.0)
    assert rl.allow("a", 3.0 + wait) is True


def test_retry_after_waits_for_enough_units_for_large_cost():
    rl = RateLimiter(4, 10.0)
    rl.allow("a", 0.0, 1)  # expires at 10
    rl.allow("a", 2.0, 1)  # expires at 12
    rl.allow("a", 4.0, 2)  # expires at 14
    # used = 4, cost 3 needs 3 units freed: first two (1+1) are not enough,
    # need third entry (t=4) => wait until 14
    assert rl.retry_after("a", 5.0, 3) == pytest.approx(9.0)
    # cost 2 needs 2 units freed: t=0 and t=2 => wait until 12
    assert rl.retry_after("a", 5.0, 2) == pytest.approx(7.0)


def test_retry_after_cost_one_frees_oldest_first():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 3.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)
    assert rl.retry_after("a", 10.0) == pytest.approx(0.0)


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    for _ in range(3):
        assert rl.retry_after("a", 1.0) == pytest.approx(9.0)
    assert rl.allow("a", 10.0) is True


def test_retry_after_returns_float():
    rl = RateLimiter(1, 10)
    rl.allow("a", 0)
    assert isinstance(rl.retry_after("a", 4), float)
    assert rl.retry_after("a", 4) == pytest.approx(6.0)
    assert isinstance(rl.retry_after("b", 4), float)


# --- time monotonicity ---

def test_time_going_backwards_raises_for_allow():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.999)


def test_time_going_backwards_raises_across_clients():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 1.0)


def test_time_going_backwards_raises_for_remaining_and_retry_after():
    rl = RateLimiter(5, 10.0)
    rl.remaining("a", 5.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 4.0)


def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is True
    assert rl.allow("a", 5.0) is False
    assert rl.remaining("b", 5.0) == 2


def test_backwards_time_does_not_record_or_move_clock():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    # clock still at 5.0: a request at 5.0 is still rejected (budget used)
    assert rl.allow("a", 5.0) is False
    assert rl.remaining("a", 5.0) == 0


def test_time_check_is_applied_after_cost_check():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0, 0)
    # bad cost raised ValueError; the clock must still allow t=5.0
    assert rl.remaining("a", 5.0) == 1
