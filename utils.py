import threading
from time import time
from typing import Dict

class RateLimiter:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown = cooldown_seconds
        self.last_request_time: Dict[str, Dict[str, float]] = {}
        self.lock = threading.Lock()

    def can_make_request(self, user_id: str, report_key: str) -> bool:
        with self.lock:
            current_time = time()
            if user_id not in self.last_request_time:
                self.last_request_time[user_id] = {}

            if report_key not in self.last_request_time[user_id]:
                self.last_request_time[user_id][report_key] = current_time
                return True

            time_passed = current_time - self.last_request_time[user_id][report_key]
            if time_passed >= self.cooldown:
                self.last_request_time[user_id][report_key] = current_time
                return True
            return False
from typing import Dict
from time import time

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
