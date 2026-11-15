class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be > 0")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client_id -> list of (time, cost), chronological
        self._latest = None

    def _check_cost(self, cost):
        if isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _advance(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        events = [e for e in self._events.get(client_id, []) if now - e[0] < self._window]
        if client_id in self._events:
            self._events[client_id] = events
        return events

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._advance(now)
        events = self._active(client_id, now)
        if sum(c for _, c in events) + cost > self._limit:
            return False
        self._events.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        events = self._active(client_id, now)
        return self._limit - sum(c for _, c in events)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._advance(now)
        events = self._active(client_id, now)
        used = sum(c for _, c in events)
        need = used + cost - self._limit
        if need <= 0:
            return 0.0
        freed = 0
        for t, c in events:
            freed += c
            if freed >= need:
                return max(0.0, float(t + self._window - now))
        return 0.0
