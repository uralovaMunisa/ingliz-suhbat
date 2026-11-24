import time
from services.rate_limiter import RateLimiter

def test_rate_limiter_allowed_and_blocked():
    # 3 requests per 2 seconds
    limiter = RateLimiter(max_requests=3, window_seconds=2)
    user_id = 999

    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is True

    # 4th request must be rejected
    assert limiter.is_allowed(user_id) is False
    assert limiter.remaining_seconds(user_id) > 0

    # Sleep for window to expire
    time.sleep(2.1)
    assert limiter.is_allowed(user_id) is True


def test_rate_limiter_multiple_users():
    limiter = RateLimiter(max_requests=2, window_seconds=5)
    user1 = 101
    user2 = 102

    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is False

    # user2 should still be allowed independently
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is False

