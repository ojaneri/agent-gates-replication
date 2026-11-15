class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number > 0")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> list of (time, cost) in non-decreasing time order
        self._records = {}
        self._max_now = None

    # ----- internal helpers -------------------------------------------------

    def _check_cost(self, cost: int) -> None:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if cost < 1 or cost > self._limit:
            raise ValueError("cost must be between 1 and limit")

    def _check_time(self, now: float) -> None:
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        if self._max_now is None or now > self._max_now:
            self._max_now = now

    def _active(self, client_id: str, now: float) -> list:
        """Return the client's requests still inside the window at `now`,
        pruning expired ones from storage (safe: time never goes backwards)."""
        entries = self._records.get(client_id)
        if not entries:
            return []
        active = [(t, c) for (t, c) in entries if now - t < self._window]
        if active:
            self._records[client_id] = active
        else:
            del self._records[client_id]
        return active

    # ----- public API -------------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        active = self._active(client_id, now)
        in_use = sum(c for _, c in active)
        if in_use + cost > self._limit:
            return False
        self._records.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        active = self._active(client_id, now)
        in_use = sum(c for _, c in active)
        return self._limit - in_use

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        active = self._active(client_id, now)
        in_use = sum(c for _, c in active)
        if in_use + cost <= self._limit:
            return 0.0
        # Expire the oldest active requests one by one until `cost` fits.
        # Entries are stored in time order, so the expiry of entry i is
        # t_i + window; the first point where the budget fits is the answer.
        for t, c in active:
            in_use -= c
            if in_use + cost <= self._limit:
                return max(0.0, (t + self._window) - now)
        # Unreachable: once everything has expired, cost <= limit fits.
        return 0.0
