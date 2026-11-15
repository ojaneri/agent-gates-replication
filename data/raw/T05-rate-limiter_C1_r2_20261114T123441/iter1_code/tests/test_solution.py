import pytest

from solution import RateLimiter


@pytest.mark.parametrize("limit,win", [(0, 1), (True, 1), (1.5, 1), (1, 0), (1, -1), (1, True) if False else (2, 0)])
def test_bad_init(limit, win):
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
    assert r.allow("a", 5)
    assert not r.allow("a", 6)
    assert r.remaining("a", 6) == 0
    assert r.remaining("a", 9.9) == 0
    assert r.remaining("a", 10) == 1
    assert r.allow("a", 10)
    assert not r.allow("a", 10)


def test_clients_independent():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert r.allow("b", 0)
    assert not r.allow("a", 1)
    assert r.remaining("c", 1) == 1


def test_rejected_not_recorded():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0, 2)
    assert not r.allow("a", 1)
    assert r.remaining("a", 10) == 2


def test_retry_after():
    r = RateLimiter(3, 10)
    assert r.retry_after("a", 0) == 0.0
    r.allow("a", 0, 1)
    r.allow("a", 4, 1)
    r.allow("a", 6, 1)
    assert r.retry_after("a", 7) == 3.0
    assert r.retry_after("a", 7, 2) == 7.0
    assert r.retry_after("a", 7, 3) == 9.0
    assert r.remaining("a", 7) == 0
    assert r.retry_after("a", 10) == 0.0


def test_time_backwards():
    r = RateLimiter(2, 10)
    r.allow("a", 5)
    with pytest.raises(ValueError):
        r.allow("b", 4)
    with pytest.raises(ValueError):
        r.remaining("a", 4)
    with pytest.raises(ValueError):
        r.retry_after("a", 4)
    assert r.allow("b", 5)
