import pytest

from solution import RateLimiter


@pytest.mark.parametrize("limit", [0, -1, 1.5, True, "3"])
def test_bad_limit(limit):
    with pytest.raises(ValueError):
        RateLimiter(limit, 10)


@pytest.mark.parametrize("w", [0, -1])
def test_bad_window(w):
    with pytest.raises(ValueError):
        RateLimiter(1, w)


@pytest.mark.parametrize("cost", [0, -1, 4, True, 1.0])
def test_bad_cost(cost):
    r = RateLimiter(3, 10)
    with pytest.raises(ValueError):
        r.allow("a", 0, cost)
    with pytest.raises(ValueError):
        r.retry_after("a", 0, cost)


def test_limit_one_and_cost_equal_limit():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0, 1)
    r2 = RateLimiter(3, 10)
    assert r2.allow("a", 0, 3)
    assert not r2.allow("a", 0)


def test_basic_allow_and_reject():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0)
    assert r.allow("a", 1)
    assert not r.allow("a", 2)
    assert r.remaining("a", 2) == 0


def test_rejected_not_recorded():
    r = RateLimiter(2, 10)
    assert r.allow("a", 0)
    assert r.allow("a", 1)
    assert not r.allow("a", 5)
    assert r.allow("a", 10)  # first expired exactly at 10
    assert not r.allow("a", 10)


def test_boundary_expiry():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert not r.allow("a", 9.99)
    assert r.allow("a", 10)


def test_clients_independent():
    r = RateLimiter(1, 10)
    assert r.allow("a", 0)
    assert r.allow("b", 0)
    assert r.remaining("c", 0) == 1
    assert r.remaining("a", 0) == 0


def test_cost_and_remaining():
    r = RateLimiter(5, 10)
    assert r.allow("a", 0, 2)
    assert r.remaining("a", 0) == 3
    assert not r.allow("a", 1, 4)
    assert r.remaining("a", 1) == 3
    assert r.allow("a", 1, 3)
    assert r.remaining("a", 10) == 2
    assert r.remaining("a", 11) == 5


def test_remaining_records_nothing():
    r = RateLimiter(2, 10)
    r.remaining("a", 0)
    assert r.remaining("a", 0) == 2


def test_retry_after():
    r = RateLimiter(3, 10)
    assert r.retry_after("a", 0) == 0.0
    r.allow("a", 0, 1)
    r.allow("a", 2, 1)
    r.allow("a", 4, 1)
    assert r.retry_after("a", 5) == 5.0
    assert r.retry_after("a", 5, 2) == 7.0
    assert r.retry_after("a", 5, 3) == 9.0
    assert r.retry_after("a", 5, 3) == 9.0  # records nothing
    assert isinstance(r.retry_after("a", 5), float)
    assert r.retry_after("a", 10) == 0.0


def test_retry_after_zero_when_fits():
    r = RateLimiter(3, 10)
    r.allow("a", 0, 1)
    assert r.retry_after("a", 1, 2) == 0.0
    assert r.retry_after("a", 1, 3) == 9.0


def test_time_backwards():
    r = RateLimiter(3, 10)
    r.allow("a", 5)
    with pytest.raises(ValueError):
        r.allow("b", 4)
    with pytest.raises(ValueError):
        r.remaining("a", 4)
    with pytest.raises(ValueError):
        r.retry_after("c", 4)
    assert r.allow("a", 5)
    assert r.remaining("a", 5) == 1
