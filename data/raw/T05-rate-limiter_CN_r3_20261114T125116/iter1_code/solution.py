from collections import deque


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number > 0")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client_id -> deque of (time, cost)
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or not (1 <= cost <= self._limit):
            raise ValueError("cost must be an integer from 1 to limit")

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _prune(self, client_id, now):
        dq = self._events.get(client_id)
        if dq is None:
            return None
        while dq and now - dq[0][0] >= self._window:
            dq.popleft()
        return dq

    def _used(self, dq):
        return sum(c for _, c in dq) if dq else 0

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        dq = self._prune(client_id, now)
        if self._used(dq) + cost > self._limit:
            return False
        if dq is None:
            dq = self._events[client_id] = deque()
        dq.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        dq = self._prune(client_id, now)
        return self._limit - self._used(dq)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        dq = self._prune(client_id, now)
        used = self._used(dq)
        if used + cost <= self._limit:
            return 0.0
        for t, c in dq:
            used -= c
            if used + cost <= self._limit:
                return max(0.0, float(t + self._window - now))
        return 0.0
