import pytest

from solution import RateLimiter


@pytest.mark.parametrize("limit,window", [(0, 10), (True, 10), (1.5, 10), (1, 0), (1, -1)])
def test_invalid_constructor(limit, window):
    with pytest.raises(ValueError):
        RateLimiter(limit, window)


def test_fractional_window_is_valid():
    r = RateLimiter(1, 0.5)
    assert r.allow("a", 0) is True
    assert r.allow("a", 0.25) is False
    assert r.allow("a", 0.5) is True


def test_basic_limit():
    r = RateLimiter(3, 10)
    assert [r.allow("a", t) for t in (0, 1, 2, 3)] == [True, True, True, False]


def test_window_boundary_is_half_open():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0) is True
    assert r.allow("a", 9.5) is False
    assert r.allow("a", 10) is True


def test_rejected_requests_do_not_count():
    r = RateLimiter(2, 10)
    assert [r.allow("a", t) for t in (0, 1, 2, 3)] == [True, True, False, False]
    assert r.allow("a", 10) is True      # only t=1 still counts
    assert r.allow("a", 10.5) is False   # t=1 and t=10 count


def test_costs():
    r = RateLimiter(5, 10)
    assert r.allow("a", 0, cost=3) is True
    assert r.allow("a", 1, cost=3) is False
    assert r.allow("a", 1, cost=2) is True
    assert r.remaining("a", 1) == 0


@pytest.mark.parametrize("cost", [0, -1, True, 1.0, 6])
def test_invalid_cost(cost):
    r = RateLimiter(5, 10)
    with pytest.raises(ValueError):
        r.allow("a", 0, cost=cost)


def test_invalid_cost_in_retry_after():
    with pytest.raises(ValueError):
        RateLimiter(5, 10).retry_after("a", 0, cost=6)


def test_clients_are_independent():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0) is True
    assert r.allow("b", 0) is True
    assert r.allow("a", 1) is False
    assert r.remaining("b", 1) == 0
    assert r.remaining("c", 1) == 1


def test_time_backwards_raises_across_clients_and_methods():
    r = RateLimiter(2, 10)
    r.allow("a", 5)
    with pytest.raises(ValueError):
        r.allow("a", 4)
    with pytest.raises(ValueError):
        r.allow("b", 4)
    with pytest.raises(ValueError):
        r.remaining("a", 4.9)
    with pytest.raises(ValueError):
        r.retry_after("a", 4.9)


def test_equal_times_are_fine():
    r = RateLimiter(2, 10)
    assert r.allow("a", 3) and r.allow("a", 3)
    assert r.allow("a", 3) is False


def test_remaining_expires_and_records_nothing():
    r = RateLimiter(3, 10)
    r.allow("a", 0)
    r.allow("a", 2)
    assert r.remaining("a", 5) == 1
    assert r.remaining("a", 5) == 1
    assert r.remaining("a", 10) == 2
    assert r.remaining("a", 12) == 3


def test_retry_after_simple():
    r = RateLimiter(2, 10)
    r.allow("a", 0)
    r.allow("a", 4)
    assert r.retry_after("a", 5) == pytest.approx(5.0)
    assert r.retry_after("a", 5, cost=2) == pytest.approx(9.0)
    assert r.retry_after("other", 5) == 0.0


def test_retry_after_returns_float():
    # spec.md: "Times are floats" and retry_after(...) -> float. In-domain (float) inputs only:
    # integer times are outside the specified input type (see protocol/deviations.md).
    r = RateLimiter(1, 10.0)
    r.allow("a", 0.0)
    assert isinstance(r.retry_after("a", 4.0), float)
    assert isinstance(r.retry_after("b", 4.0), float)


def test_retry_after_with_costs():
    r = RateLimiter(5, 10)
    r.allow("a", 0, cost=3)
    r.allow("a", 2, cost=2)
    assert r.retry_after("a", 3, cost=1) == pytest.approx(7.0)
    assert r.retry_after("a", 3, cost=3) == pytest.approx(7.0)
    assert r.retry_after("a", 3, cost=4) == pytest.approx(9.0)


def test_retry_after_zero_when_allowed_and_records_nothing():
    r = RateLimiter(2, 10)
    r.allow("a", 0)
    assert r.retry_after("a", 1) == 0.0
    assert r.retry_after("a", 1) == 0.0
    assert r.allow("a", 1) is True
    assert r.allow("a", 1) is False
