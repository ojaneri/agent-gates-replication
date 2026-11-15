from collections import deque


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number > 0")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client -> deque of (time, cost)
        self._latest = None

    def _check(self, now, cost=None):
        if cost is not None and (not _is_int(cost) or cost < 1 or cost > self._limit):
            raise ValueError("invalid cost")
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _used(self, client_id, now):
        q = self._events.get(client_id)
        if not q:
            return 0
        while q and now - q[0][0] >= self._window:
            q.popleft()
        return sum(c for _, c in q)

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check(now, cost)
        if self._used(client_id, now) + cost > self._limit:
            return False
        self._events.setdefault(client_id, deque()).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check(now)
        return self._limit - self._used(client_id, now)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check(now, cost)
        used = self._used(client_id, now)
        if used + cost <= self._limit:
            return 0.0
        for t, c in self._events[client_id]:
            used -= c
            if used + cost <= self._limit:
                return (t + self._window) - now
        return 0.0
