import urllib.request
import sys

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/health"
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        print(r.read().decode())
except Exception as e:
    print("ERROR", e)
    raise
