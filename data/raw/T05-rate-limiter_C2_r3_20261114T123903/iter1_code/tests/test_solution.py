import pytest

from solution import RateLimiter


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "3"])
def test_bad_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 1.0)


@pytest.mark.parametrize("w", [0, -1.0])
def test_bad_window(w):
    with pytest.raises(ValueError):
        RateLimiter(1, w)


@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0, "1"])
def test_bad_cost(cost):
    r = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        r.allow("a", 0, cost)
    with pytest.raises(ValueError):
        r.retry_after("a", 0, cost)


def test_limit_one_valid_cost():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0, 1)


def test_cost_equal_limit_ok():
    r = RateLimiter(3, 10)
    assert r.allow("a", 0, 3)
    assert r.remaining("a", 0) == 0


def test_allow_and_reject():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0)
    assert r.allow("a", 1)
    assert not r.allow("a", 2)
    assert r.remaining("a", 2) == 0


def test_exact_boundary_expires():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert not r.allow("a", 9.99)
    assert r.allow("a", 10)


def test_rejected_not_recorded():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert not r.allow("a", 5)
    assert r.allow("a", 10)


def test_clients_independent():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert r.allow("b", 0)
    assert not r.allow("a", 1)


def test_cost_budget():
    r = RateLimiter(5, 10)
    assert r.allow("a", 0, 3)
    assert not r.allow("a", 1, 3)
    assert r.allow("a", 1, 2)
    assert r.remaining("a", 1) == 0
    assert r.remaining("a", 10) == 3
    assert r.remaining("a", 11) == 5


def test_remaining_records_nothing():
    r = RateLimiter(2, 10)
    assert r.remaining("a", 0) == 2
    assert r.remaining("a", 0) == 2


def test_retry_after_zero():
    r = RateLimiter(2, 10)
    assert r.retry_after("a", 0) == 0.0
    r.allow("a", 0)
    assert r.retry_after("a", 1) == 0.0


def test_retry_after_waits():
    r = RateLimiter(3, 10)
    r.allow("a", 0, 1)
    r.allow("a", 2, 1)
    r.allow("a", 4, 1)
    assert r.retry_after("a", 5) == 5.0
    assert r.retry_after("a", 5, 2) == 7.0
    assert r.retry_after("a", 5, 3) == 9.0
    assert r.remaining("a", 5) == 0
    assert r.retry_after("a", 5) == 5.0


def test_retry_after_then_allowed():
    r = RateLimiter(2, 10)
    r.allow("a", 0, 2)
    w = r.retry_after("a", 3)
    assert w == 7.0
    assert r.allow("a", 3 + w)


def test_time_backwards():
    r = RateLimiter(2, 10)
    r.allow("a", 5)
    with pytest.raises(ValueError):
        r.allow("b", 4)
    with pytest.raises(ValueError):
        r.remaining("a", 4)
    with pytest.raises(ValueError):
        r.retry_after("a", 4)
    assert r.allow("a", 5)
