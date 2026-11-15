class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) \
                or not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client_id -> list of (time, cost)
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or cost < 1 or cost > self._limit:
            raise ValueError("invalid cost")

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        ev = [e for e in self._events.get(client_id, []) if now - e[0] < self._window]
        if client_id in self._events:
            self._events[client_id] = ev
        return ev

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        ev = self._active(client_id, now)
        if sum(c for _, c in ev) + cost > self._limit:
            return False
        self._events.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        ev = self._active(client_id, now)
        return self._limit - sum(c for _, c in ev)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        ev = self._active(client_id, now)
        used = sum(c for _, c in ev)
        if used + cost <= self._limit:
            return 0.0
        for t, c in ev:  # chronological order
            used -= c
            if used + cost <= self._limit:
                return max(0.0, t + self._window - now)
        return 0.0
