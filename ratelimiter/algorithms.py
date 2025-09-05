"""
Rate Limiting Algorithms Implementation

This module contains implementations of various rate limiting algorithms:
- Token Bucket: Allows bursts while maintaining average rate
- Leaky Bucket: Smooths request rates at constant rate
- Sliding Window: Tracks requests in moving time window
- Fixed Window: Counts requests in fixed time intervals
"""

import time
import threading
from collections import deque
from typing import Optional, Dict, Any
import math


class RateLimiter:
    """Base class for rate limiters"""

    def __init__(self, rate: float, capacity: int = None):
        """
        Initialize rate limiter

        Args:
            rate: Requests per second
            capacity: Maximum burst capacity (optional)
        """
        self.rate = rate
        self.capacity = capacity or int(rate * 60)  # Default 1 minute capacity

    def allow_request(self) -> bool:
        """Check if request should be allowed"""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        raise NotImplementedError


class TokenBucket(RateLimiter):
    """Token Bucket Algorithm

    Allows bursts of requests up to bucket capacity while maintaining average rate.
    Tokens are added to the bucket at a constant rate, and each request consumes one token.
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        super().__init__(rate, capacity)
        self.tokens = float(self.capacity)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            tokens_to_add = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_update = now

            # Check if we have enough tokens
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "algorithm": "Token Bucket",
            "rate": self.rate,
            "capacity": self.capacity,
            "current_tokens": round(self.tokens, 2),
            "last_update": self.last_update
        }


class LeakyBucket(RateLimiter):
    """Leaky Bucket Algorithm

    Processes requests at a constant rate, smoothing out bursts.
    Requests arrive at variable rates but are processed at a fixed rate.
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        super().__init__(rate, capacity)
        self.queue = deque()
        self.last_leak = time.time()
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()

            # Leak water from bucket
            elapsed = now - self.last_leak
            leak_amount = elapsed * self.rate
            if leak_amount > 0:
                # Remove leaked items from queue
                while self.queue and leak_amount > 0:
                    leak_time = self.queue.popleft()
                    leak_amount -= 1
                self.last_leak = now

            # Check if bucket has space
            if len(self.queue) < self.capacity:
                self.queue.append(now)
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "algorithm": "Leaky Bucket",
            "rate": self.rate,
            "capacity": self.capacity,
            "current_level": len(self.queue),
            "last_leak": self.last_leak
        }


class SlidingWindow(RateLimiter):
    """Sliding Window Algorithm

    Tracks requests in a moving time window for more accurate rate limiting.
    Uses a deque to maintain request timestamps within the current window.
    """

    def __init__(self, rate: float, window_size: float = 60.0):
        """
        Initialize sliding window rate limiter

        Args:
            rate: Maximum requests per window
            window_size: Window size in seconds (default 60)
        """
        super().__init__(rate)
        self.window_size = window_size
        self.requests = deque()
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()

            # Remove old requests outside the window
            while self.requests and now - self.requests[0] > self.window_size:
                self.requests.popleft()

            # Check if we're within the rate limit
            if len(self.requests) < self.rate:
                self.requests.append(now)
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        now = time.time()
        # Clean up old requests for accurate count
        while self.requests and now - self.requests[0] > self.window_size:
            self.requests.popleft()

        return {
            "algorithm": "Sliding Window",
            "rate": self.rate,
            "window_size": self.window_size,
            "current_requests": len(self.requests),
            "window_start": now - self.window_size
        }


class FixedWindow(RateLimiter):
    """Fixed Window Algorithm

    Divides time into fixed intervals and counts requests within each interval.
    Simple but can allow bursts at window boundaries.
    """

    def __init__(self, rate: float, window_size: float = 60.0):
        super().__init__(rate)
        self.window_size = window_size
        self.current_window = math.floor(time.time() / window_size)
        self.request_count = 0
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()
            current_window = math.floor(now / self.window_size)

            # Reset counter if we're in a new window
            if current_window != self.current_window:
                self.current_window = current_window
                self.request_count = 0

            # Check if we're within the rate limit
            if self.request_count < self.rate:
                self.request_count += 1
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "algorithm": "Fixed Window",
            "rate": self.rate,
            "window_size": self.window_size,
            "current_window": self.current_window,
            "request_count": self.request_count
        }
