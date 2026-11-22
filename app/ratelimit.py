import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, per_minute: int, daily_cap: int, clock=time.time):
        self.per_minute, self.daily_cap, self.clock = per_minute, daily_cap, clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._day, self._day_count = None, 0
        self._lock = threading.Lock()

    def check(self, key: str) -> str | None:
        """Returns None if allowed, otherwise the reason it is blocked."""
        with self._lock:
            now = self.clock()
            day = int(now // 86400)
            if day != self._day:
                self._day, self._day_count = day, 0
            if self._day_count >= self.daily_cap:
                return "Daily demo limit reached. Please try again tomorrow."
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.per_minute:
                return "Too many requests. Please wait a minute."
            q.append(now)
            self._day_count += 1
            return None