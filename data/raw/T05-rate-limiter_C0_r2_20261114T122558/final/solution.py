from collections import deque


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = float(window_seconds)
        # client_id -> deque of (time, cost), ordered by time
        self._records = {}
        self._max_now = None

    # ----- helpers -------------------------------------------------------

    def _check_cost(self, cost) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _check_time(self, now) -> None:
        if isinstance(now, bool) or not isinstance(now, (int, float)):
            raise ValueError("now must be a number")
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time went backwards")

    def _advance(self, now) -> None:
        """Validate and record `now` as the newest time seen, then drop expired entries."""
        self._check_time(now)
        self._max_now = now if self._max_now is None else max(self._max_now, now)
        for client_id in list(self._records):
            records = self._records[client_id]
            while records and now - records[0][0] >= self._window:
                records.popleft()
            if not records:
                del self._records[client_id]

    def _in_use(self, client_id: str) -> int:
        return sum(c for _, c in self._records.get(client_id, ()))

    # ----- public API ----------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._advance(now)
        if self._in_use(client_id) + cost > self._limit:
            return False
        self._records.setdefault(client_id, deque()).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        return max(0, self._limit - self._in_use(client_id))

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._advance(now)
        in_use = self._in_use(client_id)
        if in_use + cost <= self._limit:
            return 0.0
        # Walk recorded requests oldest first; each expiry frees its units.
        # Entries are sorted by time, so the first point where the request
        # fits is the earliest possible acceptance time.
        freed = 0
        for t, c in self._records.get(client_id, ()):
            freed += c
            if in_use - freed + cost <= self._limit:
                return max(0.0, (t + self._window) - now)
        # Unreachable: cost <= limit guarantees a fit once everything expires.
        return max(0.0, (self._records[client_id][-1][0] + self._window) - now)
