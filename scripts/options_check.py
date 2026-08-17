import http.client

def main():
    conn = http.client.HTTPConnection('127.0.0.1', 8001, timeout=10)
    conn.request('OPTIONS', '/api/v1/auth/login', headers={
        'Origin': 'http://127.0.0.1:5176',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'
    })
    resp = conn.getresponse()
    print('STATUS', resp.status, resp.reason)
    for k, v in resp.getheaders():
        print(k+':', v)
    print('\nBODY:\n', resp.read())

if __name__ == '__main__':
    main()
