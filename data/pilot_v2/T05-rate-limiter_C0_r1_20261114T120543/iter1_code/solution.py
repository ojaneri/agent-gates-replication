from collections import deque


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise ValueError("window_seconds must be a positive number")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        # client_id -> deque of (time, cost), oldest first
        self._clients = {}
        self._max_now = None

    # ----- helpers -----

    def _check_cost(self, cost) -> None:
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _check_time(self, now) -> None:
        if self._max_now is not None and now < self._max_now:
            raise ValueError("time went backwards")
        if self._max_now is None or now > self._max_now:
            self._max_now = now

    def _active(self, client_id: str, now: float) -> deque:
        """Return the client's live entries at `now`, dropping expired ones."""
        entries = self._clients.get(client_id)
        if entries is None:
            return deque()
        # Time is monotonic, so expired entries are always at the front.
        while entries and now - entries[0][0] >= self._window:
            entries.popleft()
        return entries

    @staticmethod
    def _used(entries: deque) -> int:
        return sum(c for _, c in entries)

    # ----- public API -----

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._active(client_id, now)
        if self._used(entries) + cost <= self._limit:
            entries = self._clients.setdefault(client_id, deque())
            entries.append((now, cost))
            return True
        return False

    def remaining(self, client_id: str, now: float) -> int:
        self._check_time(now)
        entries = self._active(client_id, now)
        return self._limit - self._used(entries)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._check_time(now)
        entries = self._active(client_id, now)
        used = self._used(entries)
        if used + cost <= self._limit:
            return 0.0
        # Expire the oldest entries one by one until the cost fits; the
        # moment the last required entry expires is the answer.
        for t, c in entries:
            used -= c
            if used + cost <= self._limit:
                return max(0.0, (t + self._window) - now)
        # Unreachable: cost <= limit guarantees the loop above returns.
        raise AssertionError("unreachable")
