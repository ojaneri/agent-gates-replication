from collections import deque


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client_id -> deque of (time, cost), oldest first
        self._last_now = None

    def _check_cost(self, cost: int) -> None:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if not 1 <= cost <= self._limit:
            raise ValueError("cost must be from 1 to limit")

    def _check_now(self, now: float) -> None:
        if self._last_now is not None and now < self._last_now:
            raise ValueError("time must not go backwards")
        self._last_now = now

    def _live(self, client_id: str, now: float) -> deque:
        """Drop expired records of one client and return its live records."""
        events = self._events.get(client_id)
        if events is None:
            return deque()
        while events and now - events[0][0] >= self._window:
            events.popleft()
        return events

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_now(now)
        used = sum(c for _, c in self._live(client_id, now))
        if used + cost > self._limit:
            return False
        self._events.setdefault(client_id, deque()).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_now(now)
        used = sum(c for _, c in self._live(client_id, now))
        return self._limit - used

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_now(now)
        events = self._live(client_id, now)
        used = sum(c for _, c in events)
        if used + cost <= self._limit:
            return 0.0
        needed = used + cost - self._limit  # units that must expire
        freed = 0
        for t, c in events:
            freed += c
            if freed >= needed:
                break
        # `needed <= used` because cost <= limit, so the loop always breaks.
        return float(t + self._window - now)
