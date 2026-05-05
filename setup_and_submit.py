# -*- coding: utf-8 -*-
import jwt, time, requests, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

KEY_ID = 'WDXGY9WX55'
ISSUER = '2be0734f-943a-4d61-9dc9-5d9045c46fec'
p8 = open('C:/Users/Windows/Downloads/AuthKey_WDXGY9WX55.p8').read()
APP_ID = '6764717589'

def make_token():
    return jwt.encode({'iss': ISSUER, 'iat': int(time.time()), 'exp': int(time.time()) + 1200, 'aud': 'appstoreconnect-v1'}, p8, algorithm='ES256', headers={'kid': KEY_ID})

def api(method, path, payload=None):
    h = {'Authorization': f'Bearer {make_token()}', 'Content-Type': 'application/json; charset=utf-8'}
    kw = {}
    if payload:
        kw['data'] = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    return requests.request(method, f'https://api.appstoreconnect.apple.com/v1{path}', headers=h, **kw)

# === 1. Get version ===
r = api('GET', f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=1')
v = r.json()['data'][0]
VERSION_ID = v['id']
print(f'Version: {VERSION_ID} state={v["attributes"]["appStoreState"]}')

# === 2. Set copyright ===
r = api('PATCH', f'/appStoreVersions/{VERSION_ID}', {
    'data': {'type': 'appStoreVersions', 'id': VERSION_ID, 'attributes': {'copyright': '2026 tokyonasu'}}
})
print(f'Copyright: {r.status_code}')

# === 3. Get/create localizations and set descriptions ===
r = api('GET', f'/appStoreVersions/{VERSION_ID}/appStoreVersionLocalizations')
locs = r.json()['data']
print(f'Localizations: {[l["attributes"]["locale"] for l in locs]}')

desc_ja = (
    "撮った写真に住所が入る。それだけ。\n\n"
    "カメラで撮影すると、現在地の住所・郵便番号・近くのランドマークを写真に重ねて保存。\n\n"
    "【使い方】\n"
    "1. アプリを開く\n"
    "2. シャッターを押す\n"
    "3. 住所入り写真がカメラロールに保存\n\n"
    "【表示される情報】\n"
    "- 住所（都道府県〜番地）\n"
    "- 郵便番号\n"
    "- 最寄りの駅・公園・施設名\n\n"
    "不動産の現地調査、工事現場の記録、旅行の思い出、散歩の記録に。"
)
keywords_ja = "カメラ,住所,写真,位置情報,GPS,不動産,現場,記録,地図,ランドマーク"

desc_en = (
    "Photos with addresses. Simple as that.\n\n"
    "Take a photo and it automatically saves with the current address, postal code, and nearby landmarks overlaid.\n\n"
    "HOW TO USE\n"
    "1. Open the app\n"
    "2. Tap the shutter\n"
    "3. Photo with address saved to camera roll\n\n"
    "WHAT'S SHOWN\n"
    "- Full address\n"
    "- Postal code\n"
    "- Nearest station, park, or facility\n\n"
    "Perfect for real estate inspections, construction site records, travel memories, and walk logs."
)
keywords_en = "camera,address,photo,location,GPS,real estate,site,record,map,landmark"

SUPPORT_URL = 'https://snarfnet.github.io/CameraAddressApp/'
MARKETING_URL = 'https://snarfnet.github.io/CameraAddressApp/'

for loc in locs:
    loc_id = loc['id']
    locale = loc['attributes']['locale']
    is_ja = locale == 'ja'

    payload = {
        'data': {
            'type': 'appStoreVersionLocalizations', 'id': loc_id,
            'attributes': {
                'description': desc_ja if is_ja else desc_en,
                'keywords': keywords_ja if is_ja else keywords_en,
                'supportUrl': SUPPORT_URL,
                'marketingUrl': MARKETING_URL,
            }
        }
    }
    r = api('PATCH', f'/appStoreVersionLocalizations/{loc_id}', payload)
    print(f'Update {locale}: {r.status_code}')

# If no en locale, create one
if not any('en' in l['attributes']['locale'].lower() for l in locs):
    r = api('POST', '/appStoreVersionLocalizations', {
        'data': {
            'type': 'appStoreVersionLocalizations',
            'attributes': {'locale': 'en-US', 'description': desc_en, 'keywords': keywords_en, 'supportUrl': SUPPORT_URL, 'marketingUrl': MARKETING_URL},
            'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': VERSION_ID}}}
        }
    })
    print(f'Create en-US: {r.status_code}')

# === 4. Privacy URL on appInfoLocalizations ===
r = api('GET', f'/apps/{APP_ID}/appInfos')
info_id = r.json()['data'][0]['id']
r = api('GET', f'/appInfos/{info_id}/appInfoLocalizations')
for il in r.json()['data']:
    il_id = il['id']
    locale = il['attributes']['locale']
    r2 = api('PATCH', f'/appInfoLocalizations/{il_id}', {
        'data': {'type': 'appInfoLocalizations', 'id': il_id, 'attributes': {'privacyPolicyUrl': 'https://snarfnet.github.io/CameraAddressApp/privacy'}}
    })
    print(f'Privacy URL ({locale}): {r2.status_code}')

# === 5. Content rights ===
r = api('PATCH', f'/apps/{APP_ID}', {
    'data': {'type': 'apps', 'id': APP_ID, 'attributes': {'contentRightsDeclaration': 'DOES_NOT_USE_THIRD_PARTY_CONTENT'}}
})
print(f'Content rights: {r.status_code}')

# === 6. Pricing (FREE) ===
r = api('GET', f'/apps/{APP_ID}/appPricePoints?filter[territory]=USA&limit=1')
free_pp = r.json()['data'][0]['id']
r = api('POST', '/appPriceSchedules', {
    'data': {
        'type': 'appPriceSchedules',
        'relationships': {
            'app': {'data': {'type': 'apps', 'id': APP_ID}},
            'baseTerritory': {'data': {'type': 'territories', 'id': 'USA'}},
            'manualPrices': {'data': [{'type': 'appPrices', 'id': '${price1}'}]}
        }
    },
    'included': [{'type': 'appPrices', 'id': '${price1}', 'relationships': {'appPricePoint': {'data': {'type': 'appPricePoints', 'id': free_pp}}}}]
})
print(f'Pricing: {r.status_code}')

# === 7. Review detail ===
r = api('POST', '/appStoreReviewDetails', {
    'data': {
        'type': 'appStoreReviewDetails',
        'attributes': {
            'contactFirstName': 'Tokyo', 'contactLastName': 'Nasu',
            'contactEmail': 'tokyonasu@yahoo.co.jp', 'contactPhone': '+81312345678',
            'demoAccountRequired': False,
            'notes': 'No sign-in required. The app is a camera that overlays the current address on photos. Requires camera and location permission to function.'
        },
        'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': VERSION_ID}}}
    }
})
print(f'Review detail: {r.status_code}')
if r.status_code not in (200, 201):
    print(r.text[:300])

# === 8. Age rating ===
r = api('GET', f'/appInfos/{info_id}/ageRatingDeclaration')
if r.status_code == 200:
    ard_id = r.json()['data']['id']
    r = api('PATCH', f'/ageRatingDeclarations/{ard_id}', {
        'data': {'type': 'ageRatingDeclarations', 'id': ard_id, 'attributes': {
            'alcoholTobaccoOrDrugUseOrReferences': 'NONE', 'contests': 'NONE',
            'gambling': False, 'gamblingSimulated': 'NONE', 'horrorOrFearThemes': 'NONE',
            'matureOrSuggestiveThemes': 'NONE', 'medicalOrTreatmentInformation': 'NONE',
            'profanityOrCrudeHumor': 'NONE', 'sexualContentGraphicAndNudity': 'NONE',
            'sexualContentOrNudity': 'NONE', 'violenceCartoonOrFantasy': 'NONE',
            'violenceRealistic': 'NONE', 'violenceRealisticProlongedGraphicOrSadistic': 'NONE',
            'unrestrictedWebAccess': False, 'seventeenPlus': False,
            'advertising': True, 'messagingAndChat': False,
            'userGeneratedContent': False, 'lootBox': False,
            'gunsOrOtherWeapons': 'NONE', 'healthOrWellnessTopics': False,
            'parentalControls': False, 'ageAssurance': False,
        }}
    })
    print(f'Age rating: {r.status_code}')

print('\nSetup complete!')
