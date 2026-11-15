from collections import deque


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a number > 0")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._history = {}
        self._max_now = None

    # ----- internal helpers -------------------------------------------------

    def _check_cost(self, cost) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _check_time(self, now) -> None:
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time must not go backwards")
        if self._max_now is None or now > self._max_now:
            self._max_now = now

    def _active(self, client_id: str, now: float) -> deque:
        """Drop expired entries for the client and return its live history."""
        history = self._history.get(client_id)
        if history is None:
            history = deque()
            self._history[client_id] = history
        while history and not (now - history[0][0] < self._window):
            history.popleft()
        return history

    @staticmethod
    def _used(history: deque) -> int:
        return sum(c for _, c in history)

    # ----- public API ---------------------------------------------------------

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        history = self._active(client_id, now)
        if self._used(history) + cost <= self._limit:
            history.append((now, cost))
            return True
        return False

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        history = self._active(client_id, now)
        return self._limit - self._used(history)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        history = self._active(client_id, now)
        used = self._used(history)
        if used + cost <= self._limit:
            return 0.0
        needed = used + cost - self._limit
        freed = 0
        # History is in time order, so entries expire oldest first.
        for t, c in history:
            freed += c
            if freed >= needed:
                return float((t + self._window) - now)
        # Unreachable: cost <= limit guarantees enough units expire.
        raise AssertionError("unreachable")
