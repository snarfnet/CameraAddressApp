import jwt, time, requests, json

p8 = open('C:/Users/Windows/Downloads/AuthKey_WDXGY9WX55.p8').read()
def tok():
    return jwt.encode({'iss': '2be0734f-943a-4d61-9dc9-5d9045c46fec', 'iat': int(time.time()), 'exp': int(time.time()) + 1200, 'aud': 'appstoreconnect-v1'}, p8, algorithm='ES256', headers={'kid': 'WDXGY9WX55'})
def h():
    return {'Authorization': 'Bearer ' + tok(), 'Content-Type': 'application/json'}

APP_ID = '6764717589'
VERSION_ID = '8c4dfc94-9314-4134-a371-36f59e8fb955'

# 1. Set category (PHOTO_AND_VIDEO)
r = requests.get(f'https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appInfos', headers=h())
info_id = r.json()['data'][0]['id']
r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/appInfos/{info_id}', headers=h(),
    json={'data': {'type': 'appInfos', 'id': info_id, 'relationships': {
        'primaryCategory': {'data': {'type': 'appCategories', 'id': 'PHOTO_AND_VIDEO'}}
    }}})
print(f'Category: {r.status_code}')

# 2. Set age rating
r = requests.get(f'https://api.appstoreconnect.apple.com/v1/appInfos/{info_id}/ageRatingDeclaration', headers=h())
if r.json().get('data'):
    ar_id = r.json()['data']['id']
    r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/ageRatingDeclarations/{ar_id}', headers=h(),
        json={'data': {'type': 'ageRatingDeclarations', 'id': ar_id, 'attributes': {
            'alcoholTobaccoOrDrugUseOrReferences': 'NONE', 'contests': 'NONE',
            'gamblingSimulated': 'NONE', 'horrorOrFearThemes': 'NONE',
            'matureOrSuggestiveThemes': 'NONE', 'medicalOrTreatmentInformation': 'NONE',
            'profanityOrCrudeHumor': 'NONE', 'sexualContentGraphicAndNudity': 'NONE',
            'sexualContentOrNudity': 'NONE', 'violenceCartoonOrFantasy': 'NONE',
            'violenceRealistic': 'NONE', 'violenceRealisticProlongedGraphicOrSadistic': 'NONE',
            'gambling': False, 'unrestrictedWebAccess': False,
            'seventeenPlus': False, 'ageAssurance': False,
            'healthOrWellnessTopics': False, 'messagingAndChat': False,
            'advertising': True, 'parentalControls': False,
            'userGeneratedContent': False, 'lootBox': False,
            'gunsOrOtherWeapons': 'NOT_APPLICABLE'
        }}})
    print(f'Age rating: {r.status_code}')
    if r.status_code != 200: print(r.text[:300])

# 3. Set content rights
r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}', headers=h(),
    json={'data': {'type': 'apps', 'id': APP_ID, 'attributes': {'contentRightsDeclaration': 'DOES_NOT_USE_THIRD_PARTY_CONTENT'}}})
print(f'Content rights: {r.status_code}')

# 4. Set pricing (free)
r = requests.get(f'https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/appPricePoints?filter[territory]=USA&limit=1', headers=h())
FREE_PP = r.json()['data'][0]['id']
print(f'Free price point: {FREE_PP}')

r = requests.post('https://api.appstoreconnect.apple.com/v1/appPriceSchedules', headers=h(),
    json={'data': {'type': 'appPriceSchedules', 'relationships': {
        'app': {'data': {'type': 'apps', 'id': APP_ID}},
        'baseTerritory': {'data': {'type': 'territories', 'id': 'USA'}},
        'manualPrices': {'data': [{'type': 'appPrices', 'id': '${price1}'}]}
    }}, 'included': [{'type': 'appPrices', 'id': '${price1}', 'attributes': {'startDate': None},
        'relationships': {'appPricePoint': {'data': {'type': 'appPricePoints', 'id': FREE_PP}}}}]})
print(f'Pricing: {r.status_code}')
if r.status_code not in (200, 201): print(r.text[:200])

# 5. Create review detail
r = requests.post('https://api.appstoreconnect.apple.com/v1/appStoreReviewDetails', headers=h(),
    data=json.dumps({'data': {'type': 'appStoreReviewDetails', 'attributes': {
        'contactFirstName': 'Snarfnet', 'contactLastName': 'Support',
        'contactEmail': 'snarfnet@gmail.com', 'contactPhone': '+81312345678',
        'demoAccountRequired': False
    }, 'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': VERSION_ID}}}}}))
print(f'Review detail: {r.status_code}')
if r.status_code not in (200, 201): print(r.text[:200])

# 6. Add EN locale
r = requests.post('https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations', headers=h(),
    json={'data': {'type': 'appStoreVersionLocalizations', 'attributes': {'locale': 'en-US'},
        'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': VERSION_ID}}}}})
print(f'EN locale: {r.status_code}')
en_loc_id = None
if r.status_code in (200, 201):
    en_loc_id = r.json()['data']['id']

# Get locale IDs
r = requests.get(f'https://api.appstoreconnect.apple.com/v1/appStoreVersions/{VERSION_ID}/appStoreVersionLocalizations', headers=h())
ja_loc_id = None
for loc in r.json()['data']:
    if loc['attributes']['locale'] == 'ja':
        ja_loc_id = loc['id']
    if loc['attributes']['locale'] == 'en-US':
        en_loc_id = loc['id']
print(f'JA loc: {ja_loc_id}')
print(f'EN loc: {en_loc_id}')

# 7. Set JA description
ja_desc = ("写真に住所を焼き込むカメラアプリ。\n\n"
    "撮影した写真にGPSから取得した住所と近隣のランドマーク（駅・公園・学校・病院など）を"
    "自動で重ねて保存します。\n\n"
    "現場写真・物件確認・旅行の記録に。撮影場所を写真そのものに残せるので、"
    "後から「ここどこだっけ？」がなくなります。\n\n"
    "【主な機能】\n"
    "・カメラ撮影＋住所自動オーバーレイ\n"
    "・近隣施設（駅500m、公園200m、学校・病院300m）を自動検出\n"
    "・撮影した写真をフォトライブラリに保存\n"
    "・シンプルな操作で誰でも使える")
ja_kw = "カメラ,住所,写真,GPS,位置情報,現場写真,地図,ランドマーク,記録,不動産"

r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{ja_loc_id}', headers=h(),
    json={'data': {'type': 'appStoreVersionLocalizations', 'id': ja_loc_id, 'attributes': {
        'description': ja_desc, 'keywords': ja_kw,
        'supportUrl': 'https://snarfnet.github.io/',
        'marketingUrl': 'https://snarfnet.github.io/',
        'promotionalText': '撮った写真に住所を焼き込む。現場写真・物件確認に。'
    }}})
print(f'JA desc: {r.status_code}')

# 8. Set EN description
en_desc = ("A camera app that stamps the address onto your photos.\n\n"
    "Automatically overlays GPS-based address and nearby landmarks "
    "(stations, parks, schools, hospitals) on each photo you take.\n\n"
    "Perfect for site documentation, property inspection, and travel records. "
    "Never forget where a photo was taken.\n\n"
    "[Features]\n"
    "- Camera with automatic address overlay\n"
    "- Nearby facility detection (stations 500m, parks 200m, schools/hospitals 300m)\n"
    "- Save photos directly to your photo library\n"
    "- Simple, intuitive interface")
en_kw = "camera,address,photo,GPS,location,site,map,landmark,record,real estate"

r = requests.patch(f'https://api.appstoreconnect.apple.com/v1/appStoreVersionLocalizations/{en_loc_id}', headers=h(),
    json={'data': {'type': 'appStoreVersionLocalizations', 'id': en_loc_id, 'attributes': {
        'description': en_desc, 'keywords': en_kw,
        'supportUrl': 'https://snarfnet.github.io/',
        'marketingUrl': 'https://snarfnet.github.io/',
        'promotionalText': 'Stamp the address directly onto your photos. Perfect for site documentation.'
    }}})
print(f'EN desc: {r.status_code}')
