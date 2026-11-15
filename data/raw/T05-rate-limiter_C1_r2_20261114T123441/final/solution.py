from collections import deque


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= self._limit:
            raise ValueError("invalid cost")

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        q = self._events.get(client_id)
        if q is None:
            return None
        while q and now - q[0][0] >= self._window:
            q.popleft()
        return q

    def _used(self, q):
        return sum(c for _, c in q) if q else 0

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        q = self._active(client_id, now)
        if self._used(q) + cost > self._limit:
            return False
        if q is None:
            q = self._events[client_id] = deque()
        q.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        return self._limit - self._used(self._active(client_id, now))

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        q = self._active(client_id, now)
        used = self._used(q)
        if used + cost <= self._limit:
            return 0.0
        for t, c in q:
            used -= c
            if used + cost <= self._limit:
                return max(0.0, t + self._window - now)
        return 0.0  # unreachable: cost <= limit
