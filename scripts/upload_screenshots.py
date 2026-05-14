import hashlib
import os
import time

import jwt
import requests

KEY_ID = 'WDXGY9WX55'
ISSUER = '2be0734f-943a-4d61-9dc9-5d9045c46fec'
APP_ID = '6764717589'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
P8_PATH = os.environ.get(
    'ASC_KEY_PATH',
    os.path.expanduser('~/.appstoreconnect/private_keys/AuthKey_WDXGY9WX55.p8')
)

p8 = open(P8_PATH).read()


def make_token():
    return jwt.encode(
        {
            'iss': ISSUER,
            'iat': int(time.time()),
            'exp': int(time.time()) + 1200,
            'aud': 'appstoreconnect-v1',
        },
        p8,
        algorithm='ES256',
        headers={'kid': KEY_ID},
    )


def headers():
    return {'Authorization': f'Bearer {make_token()}', 'Content-Type': 'application/json'}


def api(method, path, **kwargs):
    return requests.request(
        method,
        f'https://api.appstoreconnect.apple.com/v1{path}',
        headers=headers(),
        **kwargs,
    )


def get_version_id():
    r = api('GET', f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=5')
    data = r.json().get('data', [])
    if not data:
        return None, None
    for item in data:
        state = item['attributes']['appStoreState']
        if state in (
            'PREPARE_FOR_SUBMISSION',
            'DEVELOPER_REJECTED',
            'REJECTED',
            'METADATA_REJECTED',
            'READY_FOR_REVIEW',
            'UNRESOLVED_ISSUES',
            'WAITING_FOR_REVIEW',
            'IN_REVIEW',
        ):
            return item['id'], state
    # No editable version found — don't fall back to non-editable states
    return None, None


def get_localizations(version_id):
    r = api('GET', f'/appStoreVersions/{version_id}/appStoreVersionLocalizations')
    locs = {}
    for item in r.json().get('data', []):
        locs[item['attributes']['locale']] = item['id']
    return locs


def get_or_create_screenshot_set(loc_id, device_type):
    r = api('GET', f'/appStoreVersionLocalizations/{loc_id}/appScreenshotSets')
    for item in r.json().get('data', []):
        if item['attributes']['screenshotDisplayType'] == device_type:
            return item['id']
    r = api('POST', '/appScreenshotSets', json={
        'data': {
            'type': 'appScreenshotSets',
            'attributes': {'screenshotDisplayType': device_type},
            'relationships': {
                'appStoreVersionLocalization': {
                    'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id}
                }
            },
        }
    })
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
    filename = os.path.basename(filepath)
    r = api('POST', '/appScreenshots', json={
        'data': {
            'type': 'appScreenshots',
            'attributes': {'fileSize': len(data), 'fileName': filename},
            'relationships': {
                'appScreenshotSet': {'data': {'type': 'appScreenshotSets', 'id': set_id}}
            },
        }
    })
    if not r.ok:
        print(f'  Reserve failed: {r.status_code} {r.text[:200]}')
        return False

    screenshot = r.json()['data']
    screenshot_id = screenshot['id']
    for op in screenshot['attributes']['uploadOperations']:
        req_headers = {h['name']: h['value'] for h in op.get('requestHeaders', [])}
        offset = op.get('offset', 0)
        length = op.get('length', len(data))
        ur = requests.request(
            op['method'],
            op['url'],
            headers=req_headers,
            data=data[offset:offset + length],
        )
        if not ur.ok:
            print(f'  Upload chunk failed: {ur.status_code}')
            return False

    r = api('PATCH', f'/appScreenshots/{screenshot_id}', json={
        'data': {
            'type': 'appScreenshots',
            'id': screenshot_id,
            'attributes': {'uploaded': True, 'sourceFileChecksum': md5},
        }
    })
    if r.ok:
        print(f'  Uploaded: {filename}')
        return True
    print(f'  Commit failed: {r.status_code} {r.text[:200]}')
    return False


SCREENSHOTS = {
    'ja': {
        'locale': 'ja',
        'sets': {
            'APP_IPHONE_67': [f'screenshots/iphone67_ja_{i}.png' for i in range(1, 4)],
            'APP_IPHONE_61': [f'screenshots/iphone61_ja_{i}.png' for i in range(1, 4)],
        },
    },
    'en': {
        'locale': 'en-US',
        'sets': {
            'APP_IPHONE_67': [f'screenshots/iphone67_en_{i}.png' for i in range(1, 4)],
            'APP_IPHONE_61': [f'screenshots/iphone61_en_{i}.png' for i in range(1, 4)],
        },
    },
}


print(f'=== CameraAddressApp ({APP_ID}) ===')
version_id, state = get_version_id()
if not version_id:
    print('No editable version found')
    exit(1)
print(f'Version: {version_id} ({state})')

localizations = get_localizations(version_id)
if not localizations:
    print('No localization')
    exit(1)

for lang, config in SCREENSHOTS.items():
    loc_id = localizations.get(config['locale'])
    if not loc_id:
        print(f'Skipping {lang}: no {config["locale"]} localization')
        continue

    for device_type, paths in config['sets'].items():
        full_paths = [os.path.join(ROOT_DIR, p) for p in paths]
        existing = [p for p in full_paths if os.path.exists(p)]
        if not existing:
            print(f'  {lang} {device_type}: no files, skipping')
            continue
        print(f'  {lang} {device_type}: {len(existing)} screenshots')
        set_id = get_or_create_screenshot_set(loc_id, device_type)
        if not set_id:
            continue
        delete_existing(set_id)
        for path in existing:
            upload_screenshot(set_id, path)

print('Done!')
