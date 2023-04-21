import sys

import requests
import os
import time


scenes={}
scene_url={}

request_s = requests.Session()
request_t = requests.Session()

def getScenes(url):
    request_config = {"dlState": "any", "cardSize": "1", "lists": [], "isAvailable": None, "isAccessible": None,
                      "isWatched": None, "releaseMonth": "", "cast": [], "sites": [], "tags": [], "cuepoint": [],
                      "volume": 0, "sort": "release_desc", "offset": 0, "limit": 1}

    response = request_s.post(url+'/api/scene/list', json=request_config)
    if response.status_code == 200:
#        print(response.json()[)
        result = response.json()
        results = result['results']
        request_config['limit'] = 3000
        request_config['offset'] = 0
        while request_config['offset'] < results:
            print(str(request_config['offset'])+' '+str(request_config['limit'])+' ' +str(results))
            response = requests.post(url+'/api/scene/list', json=request_config)
            for s in response.json()['scenes']:
                scenes[s['scene_id']]=s
                scene_url[s['scene_url']]=s
            request_config['offset'] = request_config['offset'] + request_config['limit']

def filesList():
    request_config={"sort":"created_time_desc","state":"unmatched","createdDate":[],"resolutions":[],"framerates":[],"bitrates":[],"filename":""}

    response=request_s.post(url+'/api/files/list',json=request_config)
    if response.status_code==200:
#        print(response.json())
        return response.json()

def match(file_id,scene_id):
    try:
        requests.post(url+'/api/files/match',json={"file_id": file_id, "scene_id": scene_id})
    except requests.exceptions.RequestException as err:
        time.sleep(15)
        return

def process(api_key,stashbox_endpoint):
    print('fetching list of files')
    matches=[]
    for f in filesList():
        if f['oshash']:
            print('Querying file: ' + f['filename'] + ' querying stashdb with ohash: ' + f['oshash'])

            query="""query FindSceneByFingerprint($input: FingerprintQueryInput!) {
                    findSceneByFingerprint(fingerprint: $input) {
            id
            title
            details
            duration
            release_date
            code
            urls {
            url
            }
            studio{
              name
            }
         }
        }"""
            headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
                "ApiKey":api_key
            }
            # pad 0's at the start of the ohash, xbvr drops these if the string starts with 1 or more 0's so we need to pad the string if it's less than 16 characters

            ohash = f['oshash']
            if len(ohash)< 16:
                ohash='0000000000000000'[len(ohash) - 16:] + ohash
#            stashdb_match(ohash,f)
            tt_match(ohash,f)

def stashdb_match(ohash,f):
    response = request_t.post(stashbox_endpoint, json={'query':query,'variables':{"input":{"hash":ohash,"algorithm":"OSHASH"}}}, headers=headers)
    if response.status_code==200:
        res=response.json()['data']

        matched_scenes = []
        for s in res['findSceneByFingerprint']:
            print(str(s))

            for u in s['urls']:
                if scene_url.get(u['url']):
                    sc=scene_url[u['url']]
                    if sc['id'] not in [x['id'] for x in matched_scenes]:
                        matched_scenes.append(sc)
                    print('file: '+str(f))
                    print('scene: '+str(s))
            for sc in scene_url.values():
                if sc['site'].lower()==s['studio']['name']:
                    if sc['title']==s['title']:
                        if sc['id'] not in [x['id'] for x in matched_scenes]:
                            print(sc)
                            matched_scenes.append(sc)
        if len(matched_scenes)> 0:
            matches.append({"file":f,"matches":matched_scenes})
        if len(matched_scenes)==1:
            print('Updating scene: '+str(f['id'])+' '+matched_scenes[0]['scene_id'])
            match(f['id'],matched_scenes[0]['scene_id'])


def tt_match(ohash,f):
    try:
        response=request_t.post('https://timestamp.trade/hash_lookup?ohash='+ohash)
        if response.status_code==200:
            for r in response.json():
                for xid in r['xbvr-id']:
                    if xid in scenes:
                        match(f,xid)
    except requests.exceptions.RequestException as err:
        print(err)
        time.sleep(15)
        return






if __name__ == '__main__':
    print('syncing metadata')
    url = os.getenv('XBVR_HOST','http://127.0.0.1:9999')

    stashbox_endpoint = os.getenv('STASHDB_ENDPOINT', 'https://stashdb.org/graphql')
    api_key = os.getenv('STASHDB_KEY')

    getScenes(url)
    process(api_key,stashbox_endpoint)

