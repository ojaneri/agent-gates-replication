from collections import deque


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if not window_seconds > 0:
            raise ValueError("window_seconds must be greater than 0")
        self._limit = limit
        self._window = window_seconds
        self._clients = {}
        self._latest = None

    def _check_cost(self, cost):
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("cost must be an integer from 1 to limit")

    def _advance(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time must not go backwards")
        self._latest = now

    def _live(self, client_id, now):
        """Drop expired records for the client and return its live deque."""
        entries = self._clients.setdefault(client_id, deque())
        while entries and now - entries[0][0] >= self._window:
            entries.popleft()
        return entries

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._advance(now)
        entries = self._live(client_id, now)
        used = sum(c for _, c in entries)
        if used + cost > self._limit:
            return False
        entries.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        entries = self._live(client_id, now)
        used = sum(c for _, c in entries)
        return self._limit - used

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._advance(now)
        entries = self._live(client_id, now)
        used = sum(c for _, c in entries)
        if used + cost <= self._limit:
            return 0.0
        needed = used + cost - self._limit
        freed = 0
        for t, c in entries:
            freed += c
            if freed >= needed:
                return max(0.0, t + self._window - now)
