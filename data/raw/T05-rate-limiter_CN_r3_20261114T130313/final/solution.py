import math
from collections import deque


def _check_int(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


def _check_time(now):
    if isinstance(now, bool) or not isinstance(now, (int, float)):
        raise ValueError("now must be a real number")
    if math.isnan(now):
        raise ValueError("now must not be NaN")


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        _check_int(limit, "limit", 1)
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a real number")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._records = {}
        self._max_now = None

    # ----- helpers -------------------------------------------------------

    def _advance(self, now):
        """Validate `now` against the monotonic clock and update it."""
        _check_time(now)
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        self._max_now = now

    def _live(self, client_id, now):
        """Return the client's live records after dropping expired ones.

        Does not create an entry for an unknown client.
        """
        q = self._records.get(client_id)
        if q is None:
            return None
        while q and now - q[0][0] >= self._window:
            q.popleft()
        if not q:
            del self._records[client_id]
            return None
        return q

    def _used(self, q):
        return sum(c for _, c in q) if q else 0

    # ----- public API ----------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        _check_int(cost, "cost", 1)
        if cost > self._limit:
            raise ValueError("cost must not exceed limit")
        self._advance(now)
        q = self._live(client_id, now)
        used = self._used(q)
        if used + cost > self._limit:
            return False
        if q is None:
            q = deque()
            self._records[client_id] = q
        q.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        q = self._live(client_id, now)
        return self._limit - self._used(q)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        _check_int(cost, "cost", 1)
        if cost > self._limit:
            raise ValueError("cost must not exceed limit")
        self._advance(now)
        q = self._live(client_id, now)
        used = self._used(q)
        if used + cost <= self._limit:
            return 0.0
        # Units that must expire before `cost` fits.
        needed = used + cost - self._limit
        freed = 0
        for t, c in q:
            freed += c
            if freed >= needed:
                return max(0.0, (t + self._window) - now)
        # Unreachable: cost <= limit guarantees enough live units expire.
        return 0.0
