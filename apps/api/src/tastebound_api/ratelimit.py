from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from tastebound_api.errors import RateLimited

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def check(scope: str, identifier: str, *, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    bucket = _BUCKETS[f"{scope}:{identifier}"]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise RateLimited(
            f"Rate limit reached for {scope}. Try again after "
            f"{int(window_seconds / 60) or 1} minute(s)."
        )
    bucket.append(now)


def reset() -> None:
    _BUCKETS.clear()
