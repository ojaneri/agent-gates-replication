from collections import deque


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) \
                or not window_seconds > 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window = window_seconds
        self._events = {}  # client -> deque of (time, cost)
        self._latest = None

    def _tick(self, now):
        if self._latest is not None and now < self._latest:
            raise ValueError("time went backwards")

    def _commit_time(self, now):
        self._latest = now

    def _check_cost(self, cost):
        if not _is_int(cost) or cost < 1 or cost > self._limit:
            raise ValueError("invalid cost")

    def _prune(self, client_id, now):
        dq = self._events.get(client_id)
        if dq is None:
            return None
        while dq and now - dq[0][0] >= self._window:
            dq.popleft()
        return dq

    def _used(self, dq):
        return sum(c for _, c in dq) if dq else 0

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._tick(now)
        self._commit_time(now)
        dq = self._prune(client_id, now)
        if self._used(dq) + cost > self._limit:
            return False
        if dq is None:
            dq = self._events.setdefault(client_id, deque())
        dq.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._tick(now)
        self._commit_time(now)
        dq = self._prune(client_id, now)
        return self._limit - self._used(dq)

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._tick(now)
        self._commit_time(now)
        dq = self._prune(client_id, now)
        need = self._used(dq) + cost - self._limit
        if need <= 0:
            return 0.0
        freed = 0
        for t, c in dq:
            freed += c
            if freed >= need:
                return max(0.0, float(t + self._window - now))
        return 0.0  # unreachable
