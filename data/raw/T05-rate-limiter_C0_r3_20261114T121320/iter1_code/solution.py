class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if not (window_seconds > 0):
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> list of (time, cost) for requests accepted by that client,
        # in the order they were recorded (times are non-decreasing).
        self._entries = {}
        # Largest `now` seen by this limiter so far (across all clients).
        self._last_now = None

    # ----- helpers -------------------------------------------------------

    def _check_cost(self, cost: int) -> None:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise ValueError("cost must be an integer")
        if cost < 1 or cost > self._limit:
            raise ValueError("cost must be between 1 and limit")

    def _check_time(self, now: float) -> None:
        if self._last_now is not None and now < self._last_now:
            raise ValueError("time must not go backwards")

    def _live(self, client_id: str, now: float):
        """Return the live entries for a client at `now` (expired ones are dropped
        from storage, which is safe because `now` never decreases)."""
        entries = self._entries.get(client_id)
        if not entries:
            return []
        live = [(t, c) for (t, c) in entries if now - t < self._window]
        if live:
            self._entries[client_id] = live
        else:
            del self._entries[client_id]
        return live

    @staticmethod
    def _in_use(live) -> int:
        return sum(c for _, c in live)

    # ----- public API ----------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        self._last_now = now
        live = self._live(client_id, now)
        if self._in_use(live) + cost > self._limit:
            return False
        self._entries.setdefault(client_id, []).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        self._last_now = now
        live = self._live(client_id, now)
        return self._limit - self._in_use(live)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        self._last_now = now
        live = self._live(client_id, now)
        used = self._in_use(live)
        if used + cost <= self._limit:
            return 0.0
        # Walk forward through expiries in order until the request fits.
        for t, c in live:
            used -= c
            if used + cost <= self._limit:
                expires_at = t + self._window
                return max(0.0, expires_at - now)
        # Unreachable: once every live entry expires, cost <= limit always fits.
        return 0.0
