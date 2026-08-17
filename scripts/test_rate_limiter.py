import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

BASE = "http://127.0.0.1:8000/api/v1"


def get_token():
    payload = json.dumps({"email": "ops@shipguard.local", "password": "admin123"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE}/auth/login", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["access_token"]


def main():
    print("=== Testing AI API Key Rate Limiter ===")
    token = get_token()

    # Step 1: Check AI status and quota
    req = urllib.request.Request(f"{BASE}/ai/status", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        status_data = json.loads(resp.read().decode())
        print("AI Status & Quota:", json.dumps(status_data, indent=2))

    # Step 2: Rapidly hit /ai/chat to test rate limit threshold (limit = 15/min)
    print("\nExecuting rapid AI requests to verify rate limiter threshold (15 req/min)...")
    success_count = 0
    limited_count = 0

    chat_payload = json.dumps({"messages": [{"role": "user", "content": "Rate limit test query"}]}).encode("utf-8")

    for i in range(1, 20):
        req = urllib.request.Request(
            f"{BASE}/ai/chat",
            data=chat_payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                rem = resp.headers.get("X-RateLimit-Remaining-Minute", "N/A")
                success_count += 1
                print(f"Request #{i}: HTTP {resp.status} (Remaining Quota: {rem})")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                limited_count += 1
                retry_after = e.headers.get("Retry-After", "N/A")
                err_body = e.read().decode()
                print(f"Request #{i}: HTTP 429 TOO MANY REQUESTS! (Retry-After: {retry_after}s)")
                print(f"   Message: {err_body}")
            else:
                print(f"Request #{i}: Unexpected HTTP Error {e.code}: {e.read().decode()}")
        except Exception as e:
            print(f"Request #{i}: Network/Client Error {e}")

    print(f"\nRate Limit Enforcement Results:")
    print(f" - Allowed Requests: {success_count}")
    print(f" - Rate-Limited Requests (HTTP 429): {limited_count}")

    if limited_count > 0:
        print("\n✅ SUCCESS: Rate Limiter is actively protecting your API keys from over-usage!")
    else:
        print("\n⚠️ WARNING: Rate Limit threshold was not reached.")


if __name__ == "__main__":
    main()
