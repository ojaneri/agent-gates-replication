import pytest
from solution import RateLimiter


@pytest.mark.parametrize("limit,win", [(0, 1), (True, 1), (1.5, 1), (1, 0), (1, -1), (1, True * 0)])
def test_bad_init(limit, win):
    with pytest.raises(ValueError):
        RateLimiter(limit, win)


@pytest.mark.parametrize("cost", [0, 4, True, 1.0])
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
    assert r.retry_after("a", 2) == 8
    assert r.remaining("a", 10) == 1
    assert r.retry_after("a", 10) == 0.0
    assert r.allow("a", 10)
    assert not r.allow("a", 10)


def test_rejected_not_recorded_and_clients_independent():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0, 2)
    assert not r.allow("a", 1)
    assert r.allow("b", 1)
    assert r.remaining("a", 10) == 2
    assert r.remaining("zzz", 10) == 2


def test_retry_after_cost():
    r = RateLimiter(5, 10)
    r.allow("a", 0, 2)
    r.allow("a", 3, 2)
    assert r.retry_after("a", 4, 3) == 6
    assert r.retry_after("a", 4, 5) == 9
    assert r.retry_after("a", 4, 1) == 0.0


def test_time_backwards():
    r = RateLimiter(2, 10)
    r.allow("a", 5)
    r.allow("b", 5)
    for call in (lambda: r.allow("c", 4), lambda: r.remaining("a", 4), lambda: r.retry_after("a", 4)):
        with pytest.raises(ValueError):
            call()
    assert r.remaining("a", 5) == 1
