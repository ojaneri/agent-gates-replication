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
        self._clients = {}
        self._latest = None

    def _check_cost(self, cost: int) -> None:
        if (
            isinstance(cost, bool)
            or not isinstance(cost, int)
            or cost < 1
            or cost > self._limit
        ):
            raise ValueError("cost must be an integer from 1 to limit")

    def _touch(self, now: float) -> None:
        if self._latest is not None and now < self._latest:
            raise ValueError("time must not go backwards")
        self._latest = now

    def _active(self, client_id: str, now: float) -> list:
        """Return the client's requests still inside the window at `now`."""
        return [
            (t, c)
            for t, c in self._clients.get(client_id, [])
            if now - t < self._window
        ]

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._touch(now)
        active = self._active(client_id, now)
        self._clients[client_id] = active
        used = sum(c for _, c in active)
        if used + cost > self._limit:
            return False
        active.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._touch(now)
        used = sum(c for _, c in self._active(client_id, now))
        return self._limit - used

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._touch(now)
        active = self._active(client_id, now)
        used = sum(c for _, c in active)
        needed = used + cost - self._limit
        if needed <= 0:
            return 0.0
        freed = 0
        expiry = now
        for t, c in active:
            if freed >= needed:
                break
            freed += c
            expiry = t + self._window
        return float(expiry - now)
