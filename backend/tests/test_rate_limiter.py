from app.services.rate_limiter import AIRateLimiter


def test_rate_limiter_allows_and_tracks():
    limiter = AIRateLimiter()
    test_key = "user_test_123"

    is_limited, rem_min, rem_hr, rem_day, lim_min, lim_hr, lim_day, retry_after = limiter.is_rate_limited(test_key)
    assert not is_limited
    assert rem_min >= 0
    assert retry_after == 0


def test_rate_limiter_threshold_enforcement(monkeypatch):
    from app.config import Settings, get_settings
    
    # Create limiter with low minute limit
    limiter = AIRateLimiter()
    test_key = "user_burst_test"

    # Exhaust limit
    for _ in range(15):
        limiter.is_rate_limited(test_key)

    # 16th request must be rate limited
    is_limited, rem_min, rem_hr, rem_day, lim_min, lim_hr, lim_day, retry_after = limiter.is_rate_limited(test_key)
    assert is_limited
    assert rem_min == 0
    assert retry_after > 0


def test_rate_limiter_provider_quota():
    limiter = AIRateLimiter()
    assert limiter.check_and_record_provider_quota("gemini") is True
    assert limiter.check_and_record_provider_quota("nvidia") is True
