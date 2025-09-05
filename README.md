# Rate Limiter

A Python CLI rate limiter that implements multiple rate limiting algorithms and provides simulation capabilities.

## Features

- Multiple rate limiting algorithms:
  - Token Bucket
  - Leaky Bucket
  - Sliding Window
  - Fixed Window
- CLI interface with simulation mode
- Configurable parameters
- Real-time metrics and logging

## Installation

```bash
pip install -e .
```

## Usage

### Start Simulation
```bash
limiter start
```

### Other Commands
```bash
limiter --help
```

## Rate Limiting Algorithms

This section provides comprehensive documentation for each implemented rate limiting algorithm, including how they work, their characteristics, use cases, and trade-offs.

### Token Bucket Algorithm

**Overview**: The Token Bucket algorithm allows for bursty traffic while maintaining an average rate limit. It's based on the concept of a bucket that holds tokens, where each token represents permission to process one request.

**How It Works**:
- Tokens are added to the bucket at a constant rate (e.g., 10 tokens/second)
- Each incoming request consumes one token from the bucket
- If the bucket is empty, the request is denied
- The bucket has a maximum capacity to limit burst sizes
- Unused tokens accumulate up to the bucket's capacity

**Visual Example**:
```
Time: 0s   1s   2s   3s   4s   5s
Rate: 2/s  2/s  2/s  2/s  2/s
Bucket: [0] [2] [4] [6] [8] [10]

Request at 5.5s: ✓ (consume 1 token)
Bucket after: [9]

5 requests burst: ✓✓✓✓✓ (consume 5 tokens)
Bucket after: [4]
```

**Mathematical Model**:
- Token addition rate: `r` tokens/second
- Bucket capacity: `C` tokens
- Tokens at time `t`: `min(C, tokens + r × (t - last_update))`

**Pros**:
- ✅ Allows bursts of traffic when capacity is available
- ✅ Smooths out average rate over time
- ✅ Memory efficient (O(1) space complexity)
- ✅ Good for APIs that need to handle variable loads

**Cons**:
- ❌ Can allow large bursts if bucket is full
- ❌ Requires careful tuning of capacity parameter
- ❌ May not be suitable for strictly uniform rate requirements

**Use Cases**:
- API rate limiting with burst tolerance
- Network traffic shaping
- Database connection pooling
- CDN request limiting

**Configuration Example**:
```python
# 100 requests/minute with 20 request burst capacity
limiter = TokenBucket(rate=100/60, capacity=20)
```

---

### Leaky Bucket Algorithm

**Overview**: The Leaky Bucket algorithm smooths out traffic by processing requests at a constant rate, regardless of the input rate. It's based on the analogy of a bucket with a hole that leaks at a constant rate.

**How It Works**:
- Incoming requests are added to a queue (the bucket)
- Requests are processed ("leak out") at a constant rate
- If the bucket is full, new requests are denied
- The bucket has a fixed capacity to prevent memory issues
- Unlike Token Bucket, it doesn't accumulate "credit" for slow periods

**Visual Example**:
```
Time: 0s   1s   2s   3s   4s   5s
Leak Rate: 2/s 2/s 2/s 2/s 2/s
Bucket: [0] [0] [0] [0] [0] [0]

5 requests arrive at once:
Bucket: [5] [3] [1] [0] [0] [0]

Requests processed: ✓✓ (2 leaked out)
Remaining in bucket: [3]

Next 2 requests: ✓✓
Bucket: [3] (already at capacity, requests denied)
```

**Mathematical Model**:
- Leak rate: `r` requests/second
- Bucket capacity: `C` requests
- Processing time: `t` seconds
- Leaked requests: `min(queue_size, r × t)`

**Pros**:
- ✅ Provides strict rate limiting with no bursts
- ✅ Smooths traffic to a constant output rate
- ✅ Memory bounded with fixed capacity
- ✅ Good for resource-constrained environments

**Cons**:
- ❌ No burst tolerance - requests may be denied even during low traffic
- ❌ Can cause request queuing and increased latency
- ❌ Wastes capacity during low traffic periods
- ❌ More complex to implement than Token Bucket

**Use Cases**:
- Network traffic shaping for constant bandwidth
- CPU-bound processing pipelines
- Streaming services with constant bitrates
- IoT device communication with limited resources

**Configuration Example**:
```python
# Process 50 requests/minute maximum, queue up to 10
limiter = LeakyBucket(rate=50/60, capacity=10)
```

---

### Sliding Window Algorithm

**Overview**: The Sliding Window algorithm maintains a moving time window and tracks all requests within that window. It's more accurate than fixed windows but requires more memory for request tracking.

**How It Works**:
- Maintains a queue of request timestamps
- Removes timestamps older than the window size
- Counts requests within the current sliding window
- Allows request if count < rate limit
- Provides very accurate rate limiting over time

**Visual Example**:
```
Window Size: 60 seconds
Rate Limit: 5 requests/window

Time: 0:00     0:30     1:00     1:30     2:00
Window: [0:00-1:00] [0:30-1:30] [1:00-2:00] [1:30-2:30] [2:00-3:00]

Requests at:
0:15: ✓ (1/5)
0:20: ✓ (2/5)
0:25: ✓ (3/5)
1:05: ✓ (3/5, 0:25 expired)
1:10: ✓ (4/5)
1:15: ✓ (5/5)
1:16: ✗ (would be 6/5)
```

**Mathematical Model**:
- Window size: `W` seconds
- Rate limit: `R` requests per window
- Current time: `t`
- Valid requests: `count(timestamp ∈ [t-W, t])`
- Allow if: `valid_requests < R`

**Pros**:
- ✅ Most accurate rate limiting algorithm
- ✅ No boundary effects like Fixed Window
- ✅ Handles variable traffic patterns well
- ✅ Precise control over rate limits

**Cons**:
- ❌ Higher memory usage (O(n) where n = requests in window)
- ❌ More computationally expensive
- ❌ Memory usage scales with traffic volume
- ❌ Requires timestamp storage and cleanup

**Use Cases**:
- Financial transaction rate limiting
- Security-sensitive APIs requiring precise limits
- Real-time bidding systems
- API gateways with high accuracy requirements

**Configuration Example**:
```python
# 100 requests per minute sliding window
limiter = SlidingWindow(rate=100, window_size=60)
```

---

### Fixed Window Algorithm

**Overview**: The Fixed Window algorithm divides time into fixed intervals and counts requests within each interval. It's the simplest algorithm but can suffer from boundary effects.

**How It Works**:
- Time is divided into fixed windows (e.g., 1-minute intervals)
- Each window has its own request counter
- Counter resets at the start of each new window
- Allows request if current window counter < limit

**Visual Example**:
```
Window Size: 60 seconds
Rate Limit: 5 requests/window

Time Windows:
[00:00-01:00] [01:00-02:00] [02:00-03:00]

Requests in first window:
00:01: ✓ (1/5)
00:15: ✓ (2/5)
00:30: ✓ (3/5)
00:45: ✓ (4/5)
00:59: ✓ (5/5)

Requests in next window (01:00 reset):
01:01: ✓ (1/5)
01:02: ✓ (2/5)
...
01:05: ✓ (5/5)
01:06: ✗ (would be 6/5)
```

**Mathematical Model**:
- Window size: `W` seconds
- Rate limit: `R` requests per window
- Current window: `floor(t / W)`
- Reset condition: `current_window ≠ previous_window`
- Allow if: `counter < R`

**Boundary Effect Problem**:
```
Window 1: 00:00-01:00
Window 2: 01:00-02:00

Problem: 5 requests at 00:59 + 5 requests at 01:01 = 10 requests in 2 seconds!
This violates the intended 5 requests/minute limit.
```

**Pros**:
- ✅ Simplest algorithm to implement
- ✅ Memory efficient (O(1) space)
- ✅ Fast execution (minimal computation)
- ✅ Easy to understand and debug

**Cons**:
- ❌ Boundary effect allows bursts at window edges
- ❌ Less accurate than sliding window
- ❌ Can allow 2x the intended rate near boundaries
- ❌ Not suitable for strict rate limiting requirements

**Use Cases**:
- Simple rate limiting where accuracy is less critical
- Resource monitoring with rough limits
- Development/testing environments
- Legacy system integrations

**Configuration Example**:
```python
# 100 requests per minute fixed windows
limiter = FixedWindow(rate=100, window_size=60)
```

---

### Algorithm Comparison

| Algorithm | Accuracy | Memory | CPU | Burst Handling | Boundary Effects |
|-----------|----------|--------|-----|---------------|------------------|
| Token Bucket | Medium | O(1) | Low | Excellent | None |
| Leaky Bucket | High | O(capacity) | Medium | Poor | None |
| Sliding Window | Excellent | O(window_size × rate) | Medium | Good | None |
| Fixed Window | Poor | O(1) | Low | Poor | Severe |

**Choosing an Algorithm**:

- **Use Token Bucket** for APIs needing burst tolerance with average rate control
- **Use Leaky Bucket** for constant output rates and resource-constrained systems
- **Use Sliding Window** for financial/security systems requiring high accuracy
- **Use Fixed Window** for simple applications where occasional bursts are acceptable

### Performance Characteristics

- **Token Bucket**: Best performance, minimal memory, allows bursts
- **Leaky Bucket**: Good for smoothing, bounded memory, no bursts
- **Sliding Window**: Most accurate, higher memory usage, scales with traffic
- **Fixed Window**: Fastest, least accurate, boundary issues

All implementations are thread-safe and use appropriate locking mechanisms for concurrent access.

