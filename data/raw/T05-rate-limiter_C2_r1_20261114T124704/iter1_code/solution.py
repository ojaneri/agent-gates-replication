class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._latest = None
        self._log = {}

    def _check_cost(self, cost):
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer in 1..limit")

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")
        self._latest = now

    def _active(self, client_id, now):
        entries = [
            (t, c)
            for t, c in self._log.get(client_id, [])
            if now - t < self._window
        ]
        self._log[client_id] = entries
        return entries

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        entries = self._active(client_id, now)
        used = sum(c for _, c in entries)
        if used + cost > self._limit:
            return False
        entries.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        entries = self._active(client_id, now)
        return self._limit - sum(c for _, c in entries)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        entries = self._active(client_id, now)
        used = sum(c for _, c in entries)
        expiry = now
        for t, c in entries:
            if used + cost <= self._limit:
                break
            used -= c
            expiry = t + self._window
        return float(expiry - now)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)
