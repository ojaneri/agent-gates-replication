import math
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
        if math.isnan(window_seconds) or not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = float(window_seconds)
        # client_id -> deque of (time, cost), oldest first
        self._records = {}
        self._max_now = None

    # ----- helpers -------------------------------------------------------

    def _check_now(self, now: float) -> None:
        if isinstance(now, bool) or not isinstance(now, (int, float)):
            raise ValueError("now must be a number")
        if math.isnan(now):
            raise ValueError("now must not be NaN")
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time went backwards")
        self._max_now = float(now)

    def _check_cost(self, cost: int) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _live(self, client_id: str, now: float) -> deque:
        """Drop expired entries for the client and return its live deque."""
        records = self._records.get(client_id)
        if records is None:
            return deque()
        while records and now - records[0][0] >= self._window:
            records.popleft()
        if not records:
            del self._records[client_id]
            return deque()
        return records

    @staticmethod
    def _in_use(records) -> int:
        return sum(c for _, c in records)

    # ----- public API ----------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_now(now)
        self._check_cost(cost)
        records = self._live(client_id, now)
        if self._in_use(records) + cost > self._limit:
            return False
        records = self._records.setdefault(client_id, deque())
        records.append((float(now), cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_now(now)
        records = self._live(client_id, now)
        return self._limit - self._in_use(records)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_now(now)
        self._check_cost(cost)
        records = self._live(client_id, now)
        in_use = self._in_use(records)
        if in_use + cost <= self._limit:
            return 0.0
        # Entries expire oldest first; find the first expiry after which
        # the requested cost fits.
        freed = 0
        for t, c in records:
            freed += c
            if in_use - freed + cost <= self._limit:
                return (t + self._window) - now
        # Unreachable: cost <= limit guarantees all entries together fit.
        return 0.0  # pragma: no cover
