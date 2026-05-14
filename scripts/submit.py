import os
import sys
import time

import jwt
import requests

KEY_ID = 'WDXGY9WX55'
ISSUER = '2be0734f-943a-4d61-9dc9-5d9045c46fec'
APP_ID = '6764717589'
APP_VERSION = os.environ.get('APP_VERSION', '1.2')
BUILD_NUMBER = sys.argv[1]
PREPARE_ONLY = '--prepare-only' in sys.argv

p8 = open('/tmp/asc_key.p8').read()

EDITABLE_STATES = {
    'PREPARE_FOR_SUBMISSION',
    'DEVELOPER_REJECTED',
    'REJECTED',
    'METADATA_REJECTED',
    'READY_FOR_REVIEW',
    'UNRESOLVED_ISSUES',
    'WAITING_FOR_REVIEW',
    'IN_REVIEW',
}


def make_token():
    return jwt.encode(
        {'iss': ISSUER, 'iat': int(time.time()), 'exp': int(time.time()) + 1200, 'aud': 'appstoreconnect-v1'},
        p8, algorithm='ES256', headers={'kid': KEY_ID}
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


def require_ok(response, label, ok_statuses=(200, 201, 204)):
    if response.status_code not in ok_statuses:
        print(f'{label} failed: {response.status_code} {response.text[:4000]}')
        sys.exit(1)
    print(f'{label}: {response.status_code}')
    return response


def wait_for_exact_build():
    print(f'Waiting for build {BUILD_NUMBER} to be processed...')
    for i in range(100):
        r = api('GET', f'/builds?filter[app]={APP_ID}&filter[version]={BUILD_NUMBER}&filter[processingState]=VALID&limit=1')
        data = r.json()
        if data.get('data'):
            build = data['data'][0]
            print(f'Build ready: {build["id"]}')
            return build['id']
        print(f'  Waiting... ({i + 1}/100)')
        time.sleep(30)
    print(f'Build {BUILD_NUMBER} was not VALID after waiting. Not falling back to an older build.')
    sys.exit(1)


def find_version():
    r = api('GET', f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=50')
    require_ok(r, 'Fetch versions')
    for item in r.json().get('data', []):
        attrs = item['attributes']
        if attrs.get('versionString') == APP_VERSION:
            print(f'Found version {APP_VERSION}: {item["id"]} state={attrs["appStoreState"]}')
            return item['id'], attrs['appStoreState']
    return None, None


def create_version():
    print(f'Creating new version {APP_VERSION}...')
    r = api('POST', '/appStoreVersions', json={
        'data': {
            'type': 'appStoreVersions',
            'attributes': {'platform': 'IOS', 'versionString': APP_VERSION},
            'relationships': {'app': {'data': {'type': 'apps', 'id': APP_ID}}},
        }
    })
    if r.status_code == 409:
        print('Version already exists, fetching it again...')
        version_id, version_state = find_version()
        if version_id:
            return version_id, version_state
    require_ok(r, 'Create version')
    return r.json()['data']['id'], 'PREPARE_FOR_SUBMISSION'


build_id = wait_for_exact_build()

r = api('PATCH', f'/builds/{build_id}',
        json={'data': {'type': 'builds', 'id': build_id, 'attributes': {'usesNonExemptEncryption': False}}})
if r.status_code in (200, 204, 409):
    print(f'Export compliance: {r.status_code}')
else:
    require_ok(r, 'Export compliance')

version_id, version_state = find_version()
if version_state in ('WAITING_FOR_REVIEW', 'IN_REVIEW'):
    print(f'Already in review ({version_state}). Nothing to do.')
    sys.exit(0)

if not version_id:
    version_id, version_state = create_version()
elif version_state not in EDITABLE_STATES:
    print(f'Version {APP_VERSION} exists but is not editable: {version_state}')
    sys.exit(1)

print(f'Version ID: {version_id} state={version_state}')

r = api('PATCH', f'/appStoreVersions/{version_id}/relationships/build',
        json={'data': {'type': 'builds', 'id': build_id}})
require_ok(r, 'Build assigned', ok_statuses=(200, 204))

r = api('GET', f'/appStoreVersions/{version_id}/appStoreVersionLocalizations')
require_ok(r, 'Fetch localizations')
for loc in r.json().get('data', []):
    loc_id = loc['id']
    locale = loc['attributes']['locale']
    whats_new = 'Improved ad loading reliability.' if locale == 'en-US' else '広告表示の安定性を改善しました。'
    lr = api('PATCH', f'/appStoreVersionLocalizations/{loc_id}', json={
        'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id,
                 'attributes': {
                     'marketingUrl': 'https://snarfnet.github.io/',
                     'whatsNew': whats_new,
                 }}
    })
    if lr.status_code in (200, 204, 409):
        print(f'Localization metadata for {locale}: {lr.status_code}')
    else:
        require_ok(lr, f'Localization metadata for {locale}')

if PREPARE_ONLY:
    print('Prepare-only mode: version created and build assigned. Exiting.')
    sys.exit(0)

for state_filter in ['UNRESOLVED_ISSUES', 'READY_FOR_REVIEW']:
    r = api('GET', f'/apps/{APP_ID}/reviewSubmissions?filter[state]={state_filter}')
    require_ok(r, f'Fetch review submissions {state_filter}')
    for sub in r.json().get('data', []):
        sid = sub['id']
        st = sub['attributes']['state']
        cr = api('PATCH', f'/reviewSubmissions/{sid}', json={
            'data': {'type': 'reviewSubmissions', 'id': sid, 'attributes': {'canceled': True}}
        })
        if cr.status_code in (200, 204, 409):
            print(f'Cancel {sid} state={st}: {cr.status_code}')
        else:
            require_ok(cr, f'Cancel {sid}')

submission_id = None
for attempt in range(5):
    r = api('POST', '/reviewSubmissions', json={
        'data': {
            'type': 'reviewSubmissions',
            'relationships': {'app': {'data': {'type': 'apps', 'id': APP_ID}}},
        }
    })
    if r.status_code == 201:
        submission_id = r.json()['data']['id']
        print(f'ReviewSubmission created: {submission_id}')
        break
    print(f'Create reviewSubmission attempt {attempt + 1}/5 failed: {r.status_code} {r.text[:300]}')
    if attempt < 4:
        time.sleep(15)

if not submission_id:
    print('Could not create reviewSubmission after 5 attempts.')
    sys.exit(1)

r = api('POST', '/reviewSubmissionItems', json={
    'data': {
        'type': 'reviewSubmissionItems',
        'relationships': {
            'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': submission_id}},
            'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': version_id}},
        },
    }
})
require_ok(r, 'Add item')

r = api('PATCH', f'/reviewSubmissions/{submission_id}', json={
    'data': {
        'type': 'reviewSubmissions',
        'id': submission_id,
        'attributes': {'submitted': True},
    }
})
require_ok(r, 'Submit review')
state = r.json()['data']['attributes']['state']
print(f'Submitted! State: {state}')
