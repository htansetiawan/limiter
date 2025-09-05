#!/usr/bin/env python3
"""
Simple demonstration of rate limiting concepts
"""

import time
from ratelimiter.algorithms import TokenBucket, LeakyBucket, SlidingWindow, FixedWindow

def demonstrate_rate_limiting():
    """Simple demonstration of rate limiting behavior"""

    print("🎯 Rate Limiting Demonstration")
    print("=" * 50)

    # Scenario: 10 requests/second incoming, 5 requests/second allowed
    incoming_rate = 10  # requests per second
    allowed_rate = 5    # requests per second allowed
    duration = 2        # seconds to simulate

    print(f"Scenario: {incoming_rate} requests/second incoming, {allowed_rate} requests/second allowed")
    print(f"Duration: {duration} seconds")
    print()

    # Create rate limiter
    limiter = LeakyBucket(rate=allowed_rate, capacity=10)

    total_requests = 0
    allowed_requests = 0
    denied_requests = 0

    start_time = time.time()

    print("Simulating requests...")
    while time.time() - start_time < duration:
        total_requests += 1

        if limiter.allow_request():
            allowed_requests += 1
            print("✓"f"Request {total_requests}: ALLOWED")
        else:
            denied_requests += 1
            print("✗"f"Request {total_requests}: DENIED")

        # Wait to simulate incoming rate
        time.sleep(1.0 / incoming_rate)

    # Calculate final statistics
    actual_duration = time.time() - start_time
    actual_rate = allowed_requests / actual_duration

    print("\n📊 Final Results:")
    print(f"Total Requests: {total_requests}")
    print(f"Allowed Requests: {allowed_requests}")
    print(f"Denied Requests: {denied_requests}")
    print(f"Allow Rate: {allowed_requests/total_requests:.1%}")
    print(f"Actual Rate: {actual_rate:.2f} req/s")
    print(f"Incoming Rate: {total_requests/actual_duration:.1f} req/s")

    print("\n💡 Key Insights:")
    print(f"• You wanted {allowed_rate} requests/second")
    print(f"• You got {actual_rate:.1f} requests/second")
    print(f"• {denied_requests} requests were dropped to maintain the rate limit")

if __name__ == "__main__":
    demonstrate_rate_limiting()
