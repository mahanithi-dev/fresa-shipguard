import json
import urllib.request

url = 'http://127.0.0.1:8001/api/v1/auth/login'
data = json.dumps({"email": "fresa_admin", "password": "123"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print(resp.read().decode())
except Exception as e:
    print('ERROR', e)
