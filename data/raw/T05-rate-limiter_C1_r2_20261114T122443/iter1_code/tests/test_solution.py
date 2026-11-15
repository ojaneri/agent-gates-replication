import pytest

from solution import RateLimiter


# ----- constructor validation ---------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 1.0, "3", None, True, False])
def test_init_rejects_bad_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10.0)


@pytest.mark.parametrize("window", [0, 0.0, -1.0])
def test_init_rejects_non_positive_window(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


@pytest.mark.parametrize("window", ["10", None, True])
def test_init_rejects_non_numeric_window(window):
    with pytest.raises(ValueError):
        RateLimiter(3, window)


def test_init_accepts_int_window_and_limit_one():
    rl = RateLimiter(1, 5)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 1.0)


# ----- cost validation -----------------------------------------------------

@pytest.mark.parametrize("cost", [0, -1, 4, 1.0, True, "1", None])
def test_bad_cost_raises_in_every_method(cost):
    rl = RateLimiter(3, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", 0.0, cost)
    with pytest.raises(ValueError):
        rl.retry_after("a", 0.0, cost)


def test_cost_equal_to_limit_is_allowed():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 3)
    assert rl.remaining("a", 0.0) == 0


# ----- basic allow / remaining --------------------------------------------

def test_allow_up_to_limit_then_reject():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 1.0)
    assert rl.allow("a", 2.0)
    assert not rl.allow("a", 3.0)


def test_remaining_counts_down_and_records_nothing():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining("a", 0.0) == 3
    assert rl.remaining("a", 0.0) == 3  # calling again changes nothing
    rl.allow("a", 0.0)
    assert rl.remaining("a", 0.5) == 2
    rl.allow("a", 0.5, 2)
    assert rl.remaining("a", 0.5) == 0


def test_remaining_for_unknown_client_is_full():
    rl = RateLimiter(5, 10.0)
    assert rl.remaining("nobody", 3.0) == 5


def test_rejected_requests_use_no_budget():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0, 2)
    assert not rl.allow("a", 1.0, 1)
    assert not rl.allow("a", 2.0, 1)
    # After the first request expires, budget is fully free again,
    # proving the rejected attempts were not recorded.
    assert rl.remaining("a", 10.0) == 2
    assert rl.allow("a", 10.0, 2)


def test_rejected_large_cost_does_not_block_smaller_request():
    rl = RateLimiter(3, 10.0)
    assert rl.allow("a", 0.0, 2)
    assert not rl.allow("a", 0.0, 2)  # would need 4 > 3
    assert rl.allow("a", 0.0, 1)      # 2 + 1 fits


def test_cost_units_are_counted():
    rl = RateLimiter(5, 10.0)
    assert rl.allow("a", 0.0, 3)
    assert rl.allow("a", 0.0, 2)
    assert not rl.allow("a", 0.0, 1)


# ----- clients are independent --------------------------------------------

def test_clients_have_separate_budgets():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 0.0)
    assert rl.allow("b", 0.0)
    assert rl.remaining("a", 0.0) == 0
    assert rl.remaining("b", 0.0) == 0
    assert rl.remaining("c", 0.0) == 1


# ----- sliding window expiry ----------------------------------------------

def test_request_counts_strictly_before_window_end():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert not rl.allow("a", 9.999)


def test_request_exactly_window_old_no_longer_counts():
    rl = RateLimiter(1, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 10.0)
    assert not rl.allow("a", 10.0)


def test_window_slides_one_request_at_a_time():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 5.0)
    assert not rl.allow("a", 9.0)
    assert rl.allow("a", 10.0)       # t=0 expired, t=5 and t=10 remain
    assert not rl.allow("a", 14.0)   # 5 and 10 still in window
    assert rl.allow("a", 15.0)       # t=5 expired


def test_remaining_reflects_expiry():
    rl = RateLimiter(3, 4.0)
    rl.allow("a", 0.0)
    rl.allow("a", 1.0)
    assert rl.remaining("a", 3.0) == 1
    assert rl.remaining("a", 4.0) == 2
    assert rl.remaining("a", 4.5) == 2   # t=0 expired, t=1 still live
    assert rl.remaining("a", 5.0) == 3   # t=1 is exactly 4s old: expired
    assert rl.remaining("a", 100.0) == 3


def test_expiry_of_client_history_removes_it_cleanly():
    rl = RateLimiter(1, 1.0)
    assert rl.allow("a", 0.0)
    assert rl.allow("a", 2.0)   # old entry fully expired, history reset
    assert not rl.allow("a", 2.5)


# ----- retry_after ---------------------------------------------------------

def test_retry_after_zero_when_accepted():
    rl = RateLimiter(2, 10.0)
    assert rl.retry_after("a", 0.0) == 0.0
    rl.allow("a", 0.0)
    assert rl.retry_after("a", 0.0) == 0.0


def test_retry_after_for_full_budget():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 3.0)
    assert rl.retry_after("a", 4.0) == pytest.approx(6.0)  # t=0 expires at 10
    # at t=10 the t=0 request has expired, so one unit is free again
    assert rl.retry_after("a", 10.0) == 0.0


def test_retry_after_is_zero_exactly_when_allow_would_succeed():
    rl = RateLimiter(2, 10.0)
    rl.allow("a", 0.0)
    rl.allow("a", 3.0)
    wait = rl.retry_after("a", 4.0)
    assert wait > 0
    assert not rl.allow("a", 4.0)
    assert rl.retry_after("a", 4.0 + wait) == pytest.approx(0.0)
    assert rl.allow("a", 4.0 + wait)


def test_retry_after_for_larger_cost_waits_for_multiple_entries():
    rl = RateLimiter(5, 10.0)
    rl.allow("a", 0.0, 2)   # expires at 10
    rl.allow("a", 4.0, 2)   # expires at 14
    rl.allow("a", 6.0, 1)   # expires at 16
    # at t=7 in use = 5, need cost 3 -> need to free 3 units
    # first expiry frees 2 at t=10 (not enough), second frees 2 more at t=14
    assert rl.retry_after("a", 7.0, 3) == pytest.approx(7.0)
    # cost 1 needs one unit: first entry (cost 2) frees it at t=10
    assert rl.retry_after("a", 7.0, 1) == pytest.approx(3.0)


def test_retry_after_zero_cost_one_for_partial_free():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 0.0, 2)
    rl.allow("a", 1.0, 1)
    # need 2 units; first entry frees 2 at t=10
    assert rl.retry_after("a", 2.0, 2) == pytest.approx(8.0)


def test_retry_after_unknown_client_is_zero():
    rl = RateLimiter(1, 10.0)
    assert rl.retry_after("ghost", 5.0) == 0.0


def test_retry_after_records_nothing():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 0.0)
    rl.retry_after("a", 1.0)
    rl.retry_after("a", 2.0)
    # the calls above must not have added entries; budget frees exactly at 10
    assert rl.remaining("a", 10.0) == 1
    assert rl.allow("a", 10.0)


def test_retry_after_on_fresh_client_with_cost_at_limit():
    rl = RateLimiter(4, 10.0)
    assert rl.retry_after("x", 0.0, 4) == 0.0


# ----- time monotonicity ----------------------------------------------------

def test_time_going_backwards_raises_for_every_method():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 4.0)
    with pytest.raises(ValueError):
        rl.remaining("a", 4.0)
    with pytest.raises(ValueError):
        rl.retry_after("a", 4.0)


def test_monotonicity_is_global_across_clients():
    rl = RateLimiter(3, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("b", 4.9)
    with pytest.raises(ValueError):
        rl.remaining("never-seen", 1.0)


def test_equal_times_are_fine():
    rl = RateLimiter(2, 10.0)
    assert rl.allow("a", 7.0)
    assert rl.allow("a", 7.0)
    assert not rl.allow("a", 7.0)
    assert rl.remaining("a", 7.0) == 0


def test_rejected_backwards_call_does_not_move_clock():
    rl = RateLimiter(1, 10.0)
    rl.allow("a", 5.0)
    with pytest.raises(ValueError):
        rl.allow("a", 1.0)
    # clock is still 5.0, so 5.0 is still valid
    assert rl.remaining("a", 5.0) == 0


def test_time_must_be_a_number():
    rl = RateLimiter(1, 10.0)
    with pytest.raises(ValueError):
        rl.allow("a", "3.0")
    with pytest.raises(ValueError):
        rl.remaining("a", True)
    with pytest.raises(ValueError):
        rl.retry_after("a", None)


def test_integer_times_work():
    rl = RateLimiter(1, 10)
    assert rl.allow("a", 0)
    assert rl.allow("a", 10)
