# Sliding-window rate limiter

Implement the class `RateLimiter` in `solution.py`. Times are floats in seconds, supplied by the caller (no clock is read).

```python
RateLimiter(limit: int, window_seconds: float)
    .allow(client_id: str, now: float, cost: int = 1) -> bool
    .remaining(client_id: str, now: float) -> int
    .retry_after(client_id: str, now: float, cost: int = 1) -> float
```

## Rules

1. `limit` must be an integer of at least 1 (a `bool` is not accepted) and `window_seconds` must be greater than 0. Otherwise raise `ValueError`.
2. `cost` must be an integer from 1 to `limit` (a `bool` is not accepted). Otherwise raise `ValueError`.
3. Each client has its own budget. Clients never affect each other.
4. A request accepted at time `t` with cost `c` uses `c` units of its client's budget while `now - t < window_seconds`. A request that is exactly `window_seconds` old no longer counts.
5. `allow` accepts the request if the units in use plus `cost` do not exceed `limit`. If accepted, it records the request at `now` and returns `True`. If rejected, it returns `False` and records nothing: rejected requests never use budget.
6. `remaining` returns how many units the client could still use at `now`. It records nothing.
7. `retry_after` returns `0.0` if a request of that cost would be accepted at `now`. Otherwise it returns the number of seconds from `now` until enough of the client's recorded requests have expired for that cost to fit. It records nothing.
8. Time never goes backwards. If any method is called with a `now` smaller than the largest `now` seen so far by this limiter, for any client, raise `ValueError`. Equal times are fine.
