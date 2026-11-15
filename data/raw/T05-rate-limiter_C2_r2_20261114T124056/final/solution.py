class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}
        self._latest = None

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _check_cost(self, cost):
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("invalid cost")

    def _active(self, client_id, now):
        events = [
            (t, c)
            for t, c in self._events.get(client_id, [])
            if now - t < self._window
        ]
        self._events[client_id] = events
        return events

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        events = self._active(client_id, now)
        used = sum(c for _, c in events)
        if used + cost > self._limit:
            return False
        events.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        events = self._active(client_id, now)
        return self._limit - sum(c for _, c in events)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        events = self._active(client_id, now)
        used = sum(c for _, c in events)
        if used + cost <= self._limit:
            return 0.0
        for t, c in events:
            used -= c
            if used + cost <= self._limit:
                break
        return float(t + self._window - now)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)
