import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1"

def post_json(path, data):
    url = BASE + path
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                 headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)

def get(path, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)

def main():
    try:
        print("Logging in...")
        login = post_json('/auth/login', {"email":"ops@shipguard.local","password":"shipguard123"})
        token = login.get('access_token')
        print('Token:', bool(token))

        print('\nListing shipments (1)...')
        shipments = get('/shipments?page=1&page_size=1', token)
        items = shipments.get('items') or shipments.get('shipments') or []
        print('Shipments response keys:', list(shipments.keys()))
        ship_id = None
        if isinstance(items, list) and len(items) > 0:
            ship_id = items[0].get('id') or items[0].get('shipment_id') or items[0].get('id')
            print('Found shipment id:', ship_id)
        else:
            print('No shipments found in response')

        print('\nChecking AI status...')
        status = get('/ai/status', token)
        print('AI status:', status)

        if ship_id:
            print(f"\nRequesting explanation for shipment {ship_id}...")
            expl = get(f'/ai/explain/{ship_id}', token)
            print('Explanation:', expl)
        else:
            print('Skipping explanation (no shipment id)')

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
        except Exception:
            body = '<no body>'
        print('HTTPError', e.code, body)
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()
