import pytest
from solution import RateLimiter


@pytest.mark.parametrize("limit,win", [(0, 1), (-1, 1), (True, 1), (1.5, 1), (1, 0), (1, -2)])
def test_bad_ctor(limit, win):
    with pytest.raises(ValueError):
        RateLimiter(limit, win)


@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0])
def test_bad_cost(cost):
    r = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        r.allow("a", 0, cost)
    with pytest.raises(ValueError):
        r.retry_after("a", 0, cost)


def test_basic_and_expiry():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0)
    assert r.allow("a", 1)
    assert not r.allow("a", 2)
    assert r.remaining("a", 2) == 0
    assert r.retry_after("a", 2) == 8.0
    assert not r.allow("a", 9.99)
    assert r.allow("a", 10)  # first expired exactly
    assert r.remaining("a", 10) == 0


def test_rejected_not_recorded():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert not r.allow("a", 5)
    assert r.allow("a", 10)


def test_clients_independent():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert r.allow("b", 0)
    assert r.remaining("c", 0) == 1


def test_cost_and_retry_after():
    r = RateLimiter(5, 10)
    assert r.allow("a", 0, 2)
    assert r.allow("a", 3, 2)
    assert r.remaining("a", 3) == 1
    assert r.retry_after("a", 3, 1) == 0.0
    assert r.retry_after("a", 4, 3) == 6.0   # first expires at 10
    assert r.retry_after("a", 4, 5) == 9.0   # both must expire
    assert r.remaining("a", 4) == 1  # no recording


def test_time_backwards():
    r = RateLimiter(2, 10)
    r.allow("a", 5)
    r.allow("a", 5)
    with pytest.raises(ValueError):
        r.remaining("b", 4)
    with pytest.raises(ValueError):
        r.allow("b", 4)
    with pytest.raises(ValueError):
        r.retry_after("b", 4)
