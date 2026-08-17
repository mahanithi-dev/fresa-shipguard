import requests

url = 'http://127.0.0.1:8001/api/v1/auth/login'
payload = {'email': 'ops@shipguard.local', 'password': 'shipguard123'}
try:
    resp = requests.post(url, json=payload, timeout=10)
    print('STATUS', resp.status_code)
    print('HEADERS:')
    for k, v in resp.headers.items():
        print(f'{k}: {v}')
    print('\nBODY:\n', resp.text)
except Exception as e:
    print('ERROR', e)
