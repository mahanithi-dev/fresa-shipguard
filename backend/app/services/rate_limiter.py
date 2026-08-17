import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple
from fastapi import Depends, HTTPException, Request, Response, status

from app.config import get_settings
from app.deps import get_current_user
from app.entities import User


class AIRateLimiter:
    """In-memory sliding window rate limiter & provider quota tracker for Gemini and NVIDIA API keys."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def _clean_old(self, key: str, now: float):
        """Remove timestamps older than 24 hours (86,400 seconds)."""
        cutoff = now - 86400.0
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def is_rate_limited(self, key: str) -> Tuple[bool, int, int, int, int, int, int, int]:
        """Check if request key is rate limited across minute, hour, and day windows.

        Returns: (is_limited, remaining_min, remaining_hr, remaining_day, limit_min, limit_hr, limit_day, retry_after)
        """
        settings = get_settings()
        limit_min = settings.ai_rate_limit_per_minute
        limit_hr = settings.ai_rate_limit_per_hour
        limit_day = getattr(settings, "ai_rate_limit_per_day", 1000)
        now = time.time()

        with self._lock:
            self._clean_old(key, now)
            timestamps = self._requests[key]

            # Count requests in 60s, 3600s, 86400s
            count_min = sum(1 for t in timestamps if t > now - 60.0)
            count_hr = sum(1 for t in timestamps if t > now - 3600.0)
            count_day = len(timestamps)

            remaining_min = max(0, limit_min - count_min)
            remaining_hr = max(0, limit_hr - count_hr)
            remaining_day = max(0, limit_day - count_day)

            # Check minute limit
            if count_min >= limit_min:
                min_timestamps = [t for t in timestamps if t > now - 60.0]
                oldest_in_min = min(min_timestamps) if min_timestamps else now
                retry_after = max(1, int(60.0 - (now - oldest_in_min)))
                return True, 0, remaining_hr, remaining_day, limit_min, limit_hr, limit_day, retry_after

            # Check hour limit
            if count_hr >= limit_hr:
                hr_timestamps = [t for t in timestamps if t > now - 3600.0]
                oldest_in_hr = min(hr_timestamps) if hr_timestamps else now
                retry_after = max(1, int(3600.0 - (now - oldest_in_hr)))
                return True, remaining_min, 0, remaining_day, limit_min, limit_hr, limit_day, retry_after

            # Check day limit
            if count_day >= limit_day:
                oldest_in_day = min(timestamps) if timestamps else now
                retry_after = max(1, int(86400.0 - (now - oldest_in_day)))
                return True, remaining_min, remaining_hr, 0, limit_min, limit_hr, limit_day, retry_after

            # Record request timestamp
            self._requests[key].append(now)
            return False, remaining_min - 1, remaining_hr - 1, remaining_day - 1, limit_min, limit_hr, limit_day, 0

    def check_and_record_provider_quota(self, provider: str) -> bool:
        """Check if specific AI provider (gemini / nvidia) is within daily quota.
        If allowed, records timestamp and returns True. If limit reached, returns False.
        """
        settings = get_settings()
        now = time.time()
        key = f"provider:{provider.lower()}"

        if provider.lower() == "gemini":
            daily_limit = getattr(settings, "gemini_daily_quota", 500)
        elif provider.lower() == "nvidia":
            daily_limit = getattr(settings, "nvidia_daily_quota", 500)
        else:
            daily_limit = 500

        with self._lock:
            self._clean_old(key, now)
            timestamps = self._requests[key]
            if len(timestamps) >= daily_limit:
                return False
            self._requests[key].append(now)
            return True

    def get_quota_status(self, key: str) -> Dict:
        """Get current usage stats for user key and individual AI provider keys."""
        settings = get_settings()
        now = time.time()
        with self._lock:
            self._clean_old(key, now)
            timestamps = self._requests[key]

            count_min = sum(1 for t in timestamps if t > now - 60.0)
            count_hr = sum(1 for t in timestamps if t > now - 3600.0)
            count_day = len(timestamps)

            # Provider specific stats
            gemini_key = "provider:gemini"
            nvidia_key = "provider:nvidia"
            self._clean_old(gemini_key, now)
            self._clean_old(nvidia_key, now)

            gemini_used = len(self._requests[gemini_key])
            nvidia_used = len(self._requests[nvidia_key])

            gemini_quota = getattr(settings, "gemini_daily_quota", 500)
            nvidia_quota = getattr(settings, "nvidia_daily_quota", 500)
            day_limit = getattr(settings, "ai_rate_limit_per_day", 1000)

            return {
                "used_min": count_min,
                "limit_min": settings.ai_rate_limit_per_minute,
                "remaining_min": max(0, settings.ai_rate_limit_per_minute - count_min),
                "used_hr": count_hr,
                "limit_hr": settings.ai_rate_limit_per_hour,
                "remaining_hr": max(0, settings.ai_rate_limit_per_hour - count_hr),
                "used_day": count_day,
                "limit_day": day_limit,
                "remaining_day": max(0, day_limit - count_day),
                "providers": {
                    "gemini": {
                        "used_24h": gemini_used,
                        "daily_quota": gemini_quota,
                        "remaining_24h": max(0, gemini_quota - gemini_used)
                    },
                    "nvidia": {
                        "used_24h": nvidia_used,
                        "daily_quota": nvidia_quota,
                        "remaining_24h": max(0, nvidia_quota - nvidia_used)
                    }
                }
            }


ai_rate_limiter = AIRateLimiter()


def check_ai_rate_limit(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user)
):
    """FastAPI Dependency enforcing AI API key rate limits per user / client IP."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"user_{user.user_id}" if user else f"ip_{client_ip}"

    is_limited, rem_min, rem_hr, rem_day, limit_min, limit_hr, limit_day, retry_after = ai_rate_limiter.is_rate_limited(rate_key)

    # Set informational rate limit headers
    response.headers["X-RateLimit-Limit-Minute"] = str(limit_min)
    response.headers["X-RateLimit-Remaining-Minute"] = str(rem_min)
    response.headers["X-RateLimit-Limit-Day"] = str(limit_day)
    response.headers["X-RateLimit-Remaining-Day"] = str(rem_day)

    if is_limited:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI Rate Limit Exceeded ({limit_min}/min, {limit_day}/day). Please wait {retry_after} second(s) before making additional AI calls to protect API key quotas.",
            headers={"Retry-After": str(retry_after)}
        )
