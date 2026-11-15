from collections import deque


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float):
        if not _is_int(limit) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        if not window_seconds > 0:
            raise ValueError("window must be > 0")
        self.limit = limit
        self.window = window_seconds
        self._log: dict = {}
        self._last = None

    def _advance(self, now: float) -> None:
        if self._last is not None and now < self._last:
            raise ValueError("time went backwards")
        self._last = now

    def _entries(self, client_id: str, now: float) -> deque:
        log = self._log.setdefault(client_id, deque())
        while log and now - log[0][0] >= self.window:
            log.popleft()
        return log

    @staticmethod
    def _used(log: deque) -> int:
        return sum(c for _, c in log)

    def _check_cost(self, cost: int) -> None:
        if not _is_int(cost) or cost < 1:
            raise ValueError("cost must be an integer >= 1")
        if cost > self.limit:
            raise ValueError("cost exceeds limit")

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        self._check_cost(cost)
        self._advance(now)
        log = self._entries(client_id, now)
        if self._used(log) + cost > self.limit:
            return False
        log.append((now, cost))
        return True

    def remaining(self, client_id: str, now: float) -> int:
        self._advance(now)
        return self.limit - self._used(self._entries(client_id, now))

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        self._check_cost(cost)
        self._advance(now)
        log = self._entries(client_id, now)
        used = self._used(log)
        if used + cost <= self.limit:
            return 0.0
        for t, c in log:
            used -= c
            if used + cost <= self.limit:
                return float(t + self.window - now)
        raise AssertionError("unreachable: cost <= limit")
