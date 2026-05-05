import jwt, time, requests, os, hashlib

KEY_ID = 'WDXGY9WX55'
ISSUER = '2be0734f-943a-4d61-9dc9-5d9045c46fec'
P8_PATH = os.path.expanduser('~/.appstoreconnect/private_keys/AuthKey_WDXGY9WX55.p8')
APP_ID = '6764717589'

p8 = open(P8_PATH).read()

def make_token():
    return jwt.encode(
        {'iss': ISSUER, 'iat': int(time.time()), 'exp': int(time.time()) + 1200,
         'aud': 'appstoreconnect-v1'},
        p8, algorithm='ES256', headers={'kid': KEY_ID})

def headers():
    return {'Authorization': f'Bearer {make_token()}', 'Content-Type': 'application/json'}

def api(method, path, **kwargs):
    r = requests.request(method, f'https://api.appstoreconnect.apple.com/v1{path}',
                         headers=headers(), **kwargs)
    return r

def get_version_id():
    r = api('GET', f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=5')
    data = r.json().get('data', [])
    if not data:
        return None, None
    for d in data:
        st = d['attributes']['appStoreState']
        if st in ('PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED',
                  'METADATA_REJECTED', 'WAITING_FOR_REVIEW', 'IN_REVIEW'):
            return d['id'], st
    return data[0]['id'], data[0]['attributes']['appStoreState']

def get_localization_id(version_id):
    r = api('GET', f'/appStoreVersions/{version_id}/appStoreVersionLocalizations')
    data = r.json().get('data', [])
    return data[0]['id'] if data else None

def get_or_create_screenshot_set(loc_id, device_type):
    r = api('GET', f'/appStoreVersionLocalizations/{loc_id}/appScreenshotSets')
    for item in r.json().get('data', []):
        if item['attributes']['screenshotDisplayType'] == device_type:
            return item['id']
    r = api('POST', '/appScreenshotSets', json={
        'data': {'type': 'appScreenshotSets',
                 'attributes': {'screenshotDisplayType': device_type},
                 'relationships': {
                     'appStoreVersionLocalization': {
                         'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id}}}}})
    if r.ok:
        return r.json()['data']['id']
    print(f'  Create set failed: {r.status_code} {r.text[:200]}')
    return None

def delete_existing(set_id):
    r = api('GET', f'/appScreenshotSets/{set_id}/appScreenshots')
    for item in r.json().get('data', []):
        api('DELETE', f'/appScreenshots/{item["id"]}')
        print(f'  Deleted {item["id"][:8]}')

def upload_screenshot(set_id, filepath):
    data = open(filepath, 'rb').read()
    md5 = hashlib.md5(data).hexdigest()
    size = len(data)
    filename = os.path.basename(filepath)
    r = api('POST', '/appScreenshots', json={
        'data': {'type': 'appScreenshots',
                 'attributes': {'fileSize': size, 'fileName': filename},
                 'relationships': {
                     'appScreenshotSet': {
                         'data': {'type': 'appScreenshotSets', 'id': set_id}}}}})
    if not r.ok:
        print(f'  Reserve failed: {r.status_code} {r.text[:200]}')
        return False
    resp = r.json()['data']
    screenshot_id = resp['id']
    for op in resp['attributes']['uploadOperations']:
        url = op['url']
        req_headers = {h['name']: h['value'] for h in op.get('requestHeaders', [])}
        offset = op.get('offset', 0)
        length = op.get('length', size)
        ur = requests.request(op['method'], url, headers=req_headers,
                              data=data[offset:offset + length])
        if not ur.ok:
            print(f'  Upload chunk failed: {ur.status_code}')
            return False
    r = api('PATCH', f'/appScreenshots/{screenshot_id}', json={
        'data': {'type': 'appScreenshots', 'id': screenshot_id,
                 'attributes': {'uploaded': True, 'sourceFileChecksum': md5}}})
    if r.ok:
        print(f'  Uploaded: {filename}')
        return True
    print(f'  Commit failed: {r.status_code} {r.text[:200]}')
    return False

SCREENSHOTS = [
    ('APP_IPHONE_67', [
        'screenshots/screen_67_1.png',
        'screenshots/screen_67_2.png',
        'screenshots/screen_67_3.png',
    ]),
    ('APP_IPHONE_65', [
        'screenshots/screen_65_1.png',
        'screenshots/screen_65_2.png',
        'screenshots/screen_65_3.png',
    ]),
]

print(f'=== CameraAddressApp ({APP_ID}) ===')
version_id, state = get_version_id()
if not version_id:
    print('No editable version found')
    exit(0)
print(f'Version: {version_id} ({state})')

loc_id = get_localization_id(version_id)
if not loc_id:
    print('No localization')
    exit(0)

for device_type, paths in SCREENSHOTS:
    existing = [p for p in paths if os.path.exists(p)]
    if not existing:
        print(f'  {device_type}: no files, skipping')
        continue
    print(f'  {device_type}: {len(existing)} screenshots')
    set_id = get_or_create_screenshot_set(loc_id, device_type)
    if not set_id:
        continue
    delete_existing(set_id)
    for path in existing:
        upload_screenshot(set_id, path)

print('Done!')
