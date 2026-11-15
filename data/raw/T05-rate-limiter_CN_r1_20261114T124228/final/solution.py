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
        self._clients = {}
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= self._limit:
            raise ValueError("invalid cost")

    def _advance(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        dq = self._clients.get(client_id)
        if dq is None:
            return None
        while dq and now - dq[0][0] >= self._window:
            dq.popleft()
        return dq

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._advance(now)
        dq = self._active(client_id, now)
        if dq is None:
            dq = self._clients[client_id] = deque()
        used = sum(c for _, c in dq)
        if used + cost > self._limit:
            return False
        dq.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        dq = self._active(client_id, now)
        used = sum(c for _, c in dq) if dq else 0
        return self._limit - used

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._advance(now)
        dq = self._active(client_id, now)
        if not dq:
            return 0.0
        used = sum(c for _, c in dq)
        if used + cost <= self._limit:
            return 0.0
        for t, c in dq:
            used -= c
            if used + cost <= self._limit:
                return max(0.0, t + self._window - now)
        return 0.0
