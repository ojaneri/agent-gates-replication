from collections import deque


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if not _is_number(window_seconds) or not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._requests = {}
        self._last_now = None

    def _check_cost(self, cost) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _check_time(self, now) -> None:
        if not _is_number(now):
            raise ValueError("now must be a number")
        if self._last_now is not None and now < self._last_now:
            raise ValueError("time must not go backwards")
        self._last_now = now

    def _prune(self, client_id: str, now: float) -> deque:
        """Drop expired entries for the client and return its deque (may be empty)."""
        entries = self._requests.get(client_id)
        if entries is None:
            return deque()
        while entries and now - entries[0][0] >= self._window:
            entries.popleft()
        return entries

    @staticmethod
    def _used(entries: deque) -> int:
        return sum(cost for _, cost in entries)

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._prune(client_id, now)
        if self._used(entries) + cost > self._limit:
            return False
        if client_id not in self._requests:
            self._requests[client_id] = entries
        entries.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        entries = self._prune(client_id, now)
        return max(0, self._limit - self._used(entries))

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._prune(client_id, now)
        used = self._used(entries)
        if used + cost <= self._limit:
            return 0.0
        # Expire the oldest recorded requests one by one until the cost fits.
        for t, c in entries:
            used -= c
            if used + cost <= self._limit:
                return (t + self._window) - now
        # Unreachable: cost <= limit guarantees the cost fits once all entries expire.
        return self._window  # pragma: no cover
