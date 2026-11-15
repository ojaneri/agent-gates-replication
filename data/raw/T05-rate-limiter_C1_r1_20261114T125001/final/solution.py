class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self.limit = limit
        self.window = window_seconds
        self._events = {}
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= self.limit:
            raise ValueError("invalid cost")

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        events = [(t, c) for t, c in self._events.get(client_id, []) if now - t < self.window]
        if events:
            self._events[client_id] = events
        else:
            self._events.pop(client_id, None)
        return events

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        events = self._active(client_id, now)
        if sum(c for _, c in events) + cost > self.limit:
            return False
        self._events.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        return self.limit - sum(c for _, c in self._active(client_id, now))

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        events = self._active(client_id, now)
        used = sum(c for _, c in events)
        wait = 0.0
        for t, c in events:
            if used + cost <= self.limit:
                break
            used -= c
            wait = t + self.window - now
        return wait
