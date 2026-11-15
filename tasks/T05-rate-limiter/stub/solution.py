class RateLimiter:
    """Sliding-window rate limiter. See spec.md."""

    def __init__(self, limit: int, window_seconds: float):
        raise NotImplementedError

    def allow(self, client_id: str, now: float, cost: int = 1) -> bool:
        raise NotImplementedError

    def remaining(self, client_id: str, now: float) -> int:
        raise NotImplementedError

    def retry_after(self, client_id: str, now: float, cost: int = 1) -> float:
        raise NotImplementedError
