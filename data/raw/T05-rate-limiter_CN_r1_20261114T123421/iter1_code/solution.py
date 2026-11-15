from collections import deque


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if (
            isinstance(window_seconds, bool)
            or not isinstance(window_seconds, (int, float))
            or not window_seconds > 0
        ):
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._requests = {}
        self._last_now = None

    def _check_cost(self, cost: int) -> None:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if cost < 1 or cost > self._limit:
            raise ValueError("cost must be between 1 and limit")

    def _check_time(self, now: float) -> None:
        if self._last_now is not None and now < self._last_now:
            raise ValueError("time must not go backwards")
        self._last_now = now

    def _active(self, client_id: str, now: float) -> deque:
        """Drop expired entries for the client and return its live deque."""
        dq = self._requests.get(client_id)
        if dq is None:
            dq = deque()
            self._requests[client_id] = dq
        while dq and now - dq[0][0] >= self._window:
            dq.popleft()
        return dq

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        dq = self._active(client_id, now)
        used = sum(c for _, c in dq)
        if used + cost <= self._limit:
            dq.append((now, cost))
            return True
        return False

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        dq = self._active(client_id, now)
        used = sum(c for _, c in dq)
        return self._limit - used

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        dq = self._active(client_id, now)
        used = sum(c for _, c in dq)
        excess = used + cost - self._limit
        if excess <= 0:
            return 0.0
        # Walk recorded requests oldest first; each frees its cost when it expires.
        for t, c in dq:
            excess -= c
            if excess <= 0:
                return max(0.0, t + self._window - now)
        # Unreachable: cost <= limit guarantees all entries together suffice.
        return max(0.0, dq[-1][0] + self._window - now) if dq else 0.0
