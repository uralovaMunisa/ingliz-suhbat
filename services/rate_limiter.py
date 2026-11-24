import time
from collections import defaultdict, deque
from typing import Dict


class RateLimiter:
    """Sliding-window rate limiter per user."""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._user_requests: Dict[int, deque] = defaultdict(deque)

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        requests = self._user_requests[user_id]

        # Evict timestamps older than the window
        while requests and requests[0] <= now - self.window_seconds:
            requests.popleft()

        if len(requests) < self.max_requests:
            requests.append(now)
            return True
        return False

    def remaining_seconds(self, user_id: int) -> int:
        requests = self._user_requests[user_id]
        if not requests:
            return 0
        oldest = requests[0]
        wait = int(self.window_seconds - (time.time() - oldest))
        return max(0, wait)

