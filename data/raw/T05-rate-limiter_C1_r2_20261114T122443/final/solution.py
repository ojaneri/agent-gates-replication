from collections import deque


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first.
        self._history = {}
        self._max_now = None

    # ----- helpers -------------------------------------------------------

    def _check_cost(self, cost) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _check_time(self, now) -> None:
        if isinstance(now, bool) or not isinstance(now, (int, float)):
            raise ValueError("now must be a number")
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        self._max_now = now

    def _prune(self, client_id: str, now: float) -> deque:
        """Drop expired entries for a client and return its live history."""
        entries = self._history.get(client_id)
        if entries is None:
            return deque()
        while entries and now - entries[0][0] >= self._window:
            entries.popleft()
        if not entries:
            del self._history[client_id]
            return deque()
        return entries

    @staticmethod
    def _in_use(entries: deque) -> int:
        return sum(cost for _, cost in entries)

    # ----- public API ----------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._prune(client_id, now)
        if self._in_use(entries) + cost > self._limit:
            return False
        self._history.setdefault(client_id, deque()).append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        entries = self._prune(client_id, now)
        return self._limit - self._in_use(entries)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._prune(client_id, now)
        in_use = self._in_use(entries)
        if in_use + cost <= self._limit:
            return 0.0
        needed = in_use + cost - self._limit
        freed = 0
        for t, c in entries:
            freed += c
            if freed >= needed:
                return max(0.0, t + self._window - now)
        # Unreachable: cost <= limit guarantees enough units expire.
        return 0.0  # pragma: no cover
