from collections import deque


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if (isinstance(window_seconds, bool)
                or not isinstance(window_seconds, (int, float))
                or not window_seconds > 0):
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._events = {}
        self._max_now = None

    # ----- helpers -----

    @staticmethod
    def _check_cost(cost, limit):
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if cost < 1 or cost > limit:
            raise ValueError("cost must be between 1 and limit")

    def _check_time(self, now):
        if isinstance(now, bool) or not isinstance(now, (int, float)):
            raise ValueError("now must be a number")
        if now != now:  # NaN
            raise ValueError("now must not be NaN")
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        self._max_now = now

    def _live(self, client_id, now):
        """Drop expired entries for this client and return its deque."""
        q = self._events.get(client_id)
        if q is None:
            q = deque()
            self._events[client_id] = q
        while q and now - q[0][0] >= self._window:
            q.popleft()
        return q

    @staticmethod
    def _used(q):
        return sum(c for _, c in q)

    # ----- public API -----

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost, self._limit)
        self._check_time(now)
        q = self._live(client_id, now)
        if self._used(q) + cost <= self._limit:
            q.append((now, cost))
            return True
        return False

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        q = self._live(client_id, now)
        return self._limit - self._used(q)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost, self._limit)
        self._check_time(now)
        q = self._live(client_id, now)
        used = self._used(q)
        if used + cost <= self._limit:
            return 0.0
        # Must free at least `needed` units by expiring the oldest entries.
        needed = used + cost - self._limit
        freed = 0
        for t, c in q:
            freed += c
            if freed >= needed:
                return float(t + self._window - now)
        # Unreachable: cost <= limit guarantees enough entries expire.
        return float(self._window)
