import threading
from time import time
from typing import Dict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}

    def can_make_request(self, user_id: str, endpoint: str) -> bool:
        """Check if a request can be made based on rate limits."""
        key = f"{user_id}:{endpoint}"
        now = time()

        # Initialize or clean old requests
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key] = [t for t in self.requests[key] if t > now - 60]

        # Check rate limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False

        self.requests[key].append(now)
        return True