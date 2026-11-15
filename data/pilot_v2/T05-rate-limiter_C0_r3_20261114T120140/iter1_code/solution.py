class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> list of (time, cost), in non-decreasing time order
        self._records = {}
        self._max_now = None

    # ----- helpers -----

    def _check_cost(self, cost: int) -> None:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if cost < 1 or cost > self._limit:
            raise ValueError("cost must be between 1 and limit")

    def _observe(self, now: float) -> None:
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        self._max_now = now

    def _live(self, client_id: str, now: float):
        """Return the client's unexpired records, dropping expired ones."""
        entries = self._records.get(client_id, [])
        live = [(t, c) for (t, c) in entries if not (now - t >= self._window)]
        if live:
            self._records[client_id] = live
        else:
            self._records.pop(client_id, None)
        return live

    # ----- public API -----

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._observe(now)
        live = self._live(client_id, now)
        in_use = sum(c for (_, c) in live)
        if in_use + cost > self._limit:
            return False
        self._records.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._observe(now)
        live = self._live(client_id, now)
        in_use = sum(c for (_, c) in live)
        return self._limit - in_use

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._observe(now)
        live = self._live(client_id, now)
        in_use = sum(c for (_, c) in live)
        needed = in_use + cost - self._limit
        if needed <= 0:
            return 0.0
        freed = 0
        for (t, c) in live:  # oldest first; each expires at t + window
            freed += c
            if freed >= needed:
                return max(0.0, (t + self._window) - now)
        # Unreachable because cost <= limit guarantees enough expires.
        return max(0.0, (live[-1][0] + self._window) - now)
