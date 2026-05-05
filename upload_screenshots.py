import jwt, time, requests, json, hashlib, os

key_path = os.environ.get('ASC_KEY_PATH', 'C:/Users/Windows/Downloads/AuthKey_WDXGY9WX55.p8')
p8 = open(key_path).read()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def tok():
    return jwt.encode({'iss': '2be0734f-943a-4d61-9dc9-5d9045c46fec', 'iat': int(time.time()), 'exp': int(time.time()) + 1200, 'aud': 'appstoreconnect-v1'}, p8, algorithm='ES256', headers={'kid': 'WDXGY9WX55'})

def h():
    return {'Authorization': 'Bearer ' + tok(), 'Content-Type': 'application/json'}

APP_ID = '6764717589'

def get_version_localizations():
    """Get current version's localizations dynamically"""
    r = requests.get(f'https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=1', headers=h())
    if r.status_code != 200:
        print(f'Failed to get versions: {r.status_code} {r.text[:200]}')
        return {}
    data = r.json()
    if not data['data']:
        print('No versions found')
        return {}
    version_id = data['data'][0]['id']
    print(f'Version: {version_id}')

    r2 = requests.get(f'https://api.appstoreconnect.apple.com/v1/appStoreVersions/{version_id}/appStoreVersionLocalizations', headers=h())
    if r2.status_code != 200:
        print(f'Failed to get localizations: {r2.status_code}')
        return {}
    locs = {}
    for loc in r2.json()['data']:
        locale = loc['attributes']['locale']
        locs[locale] = loc['id']
        print(f'  Locale: {locale} -> {loc["id"]}')
    return locs

def delete_existing_screenshots(loc_id, dtype):
    """Delete existing screenshot set for this display type"""
    r = requests.get(f'https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{loc_id}/appScreenshotSets', headers=h())
    if r.status_code != 200:
        return
    for ss in r.json()['data']:
        if ss['attributes']['screenshotDisplayType'] == dtype:
            set_id = ss['id']
            # Delete all screenshots in set
            r2 = requests.get(f'https://api.appstoreconnect.apple.com/v1/appScreenshotSets/{set_id}/appScreenshots', headers=h())
            if r2.status_code == 200:
                for sc in r2.json()['data']:
                    requests.delete(f'https://api.appstoreconnect.apple.com/v1/appScreenshots/{sc["id"]}', headers=h())
            # Delete the set itself
            requests.delete(f'https://api.appstoreconnect.apple.com/v1/appScreenshotSets/{set_id}', headers=h())
            print(f'  Deleted existing set {set_id}')

def upload_screenshot(set_id, filepath):
    data = open(filepath, 'rb').read()
    fname = os.path.basename(filepath)
    md5 = hashlib.md5(data).hexdigest()
    r = requests.post('https://api.appstoreconnect.apple.com/v1/appScreenshots',
        headers=h(), json={'data': {'type': 'appScreenshots', 'attributes': {
            'fileName': fname, 'fileSize': len(data)
        }, 'relationships': {'appScreenshotSet': {'data': {'type': 'appScreenshotSets', 'id': set_id}}}}})
    if r.status_code not in (200, 201):
        print(f'  Reserve failed: {r.status_code} {r.text[:200]}')
        return False
    sc = r.json()['data']
    sc_id = sc['id']
    for op in sc['attributes']['uploadOperations']:
        part = data[op['offset']:op['offset'] + op['length']]
        hdrs = {rh['name']: rh['value'] for rh in op['requestHeaders']}
        requests.put(op['url'], headers=hdrs, data=part)
    r2 = requests.patch(f'https://api.appstoreconnect.apple.com/v1/appScreenshots/{sc_id}',
        headers=h(), json={'data': {'type': 'appScreenshots', 'id': sc_id, 'attributes': {
            'uploaded': True, 'sourceFileChecksum': md5}}})
    print(f'  Committed: {r2.status_code}')
    return r2.status_code == 200

display_types = {
    '67': 'APP_IPHONE_67',
    '61': 'APP_IPHONE_61',
}

locale_map = {'ja': 'ja', 'en': 'en-US'}

locs = get_version_localizations()
if not locs:
    print('ERROR: No localizations found, exiting')
    exit(1)

for lang, locale_key in locale_map.items():
    loc_id = locs.get(locale_key)
    if not loc_id:
        print(f'Skipping {lang}: no localization found for {locale_key}')
        continue
    for size_key, dtype in display_types.items():
        print(f'\n{lang} {dtype}:')
        delete_existing_screenshots(loc_id, dtype)
        # Create screenshot set
        r = requests.post('https://api.appstoreconnect.apple.com/v1/appScreenshotSets',
            headers=h(), json={'data': {'type': 'appScreenshotSets', 'attributes': {'screenshotDisplayType': dtype},
                'relationships': {'appStoreVersionLocalization': {'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id}}}}})
        if r.status_code in (200, 201):
            set_id = r.json()['data']['id']
            print(f'  Set created {set_id}')
        else:
            print(f'  Set creation failed {r.status_code} {r.text[:150]}')
            continue
        # Upload 3 screenshots
        for i in range(1, 4):
            path = os.path.join(SCRIPT_DIR, f'screenshots/iphone{size_key}_{lang}_{i}.png')
            if not os.path.exists(path):
                print(f'  SKIP (not found): {path}')
                continue
            print(f'  Uploading {os.path.basename(path)}...')
            upload_screenshot(set_id, path)

print('\nAll screenshots uploaded!')
