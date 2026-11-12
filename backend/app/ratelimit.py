"""In-process sliding-window rate limiter.

Fine for a single server process. With several workers or servers each keeps its own counts,
so move this to Redis before scaling out (noted in the deployment checklist).
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable

_CLEANUP_THRESHOLD = 10_000  # number of tracked keys that triggers a sweep of idle ones


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic):
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        """Records a hit if allowed. Returns (allowed, seconds_until_next_slot)."""
        now = self._clock()
        cutoff = now - self.window
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.limit:
                return False, max(0.0, hits[0] + self.window - now)

            hits.append(now)
            if len(self._hits) > _CLEANUP_THRESHOLD:
                self._sweep(cutoff)
            return True, 0.0

    def _sweep(self, cutoff: float) -> None:
        stale = [k for k, h in self._hits.items() if not h or h[-1] <= cutoff]
        for k in stale:
            del self._hits[k]


class FailureThrottle:
    """Counts failed attempts per key (for example failed logins) and blocks the key once it passes a limit.

    Unlike SlidingWindowLimiter, only failures are recorded, and a success clears the key.
    """

    def __init__(self, max_failures: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        if max_failures < 1:
            raise ValueError("max_failures must be at least 1")
        self.max_failures = max_failures
        self.window = window_seconds
        self._clock = clock
        self._fails: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _trim(self, key: str, now: float) -> deque[float]:
        fails = self._fails.get(key)
        if fails is None:
            return deque()
        while fails and fails[0] <= now - self.window:
            fails.popleft()
        if not fails:
            del self._fails[key]
            return deque()
        return fails

    def retry_after(self, key: str) -> float:
        """Seconds until the key may try again, or 0 if it is not blocked."""
        now = self._clock()
        with self._lock:
            fails = self._trim(key, now)
            if len(fails) < self.max_failures:
                return 0.0
            return max(0.0, fails[0] + self.window - now)

    def record_failure(self, key: str) -> None:
        now = self._clock()
        with self._lock:
            self._trim(key, now)
            self._fails.setdefault(key, deque()).append(now)
            if len(self._fails) > _CLEANUP_THRESHOLD:
                for k in list(self._fails):
                    self._trim(k, now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)
