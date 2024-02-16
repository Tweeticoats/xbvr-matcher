import sys

import requests
import os
import sys
import time
import base64

scenes={}
scene_url={}

request_s = requests.Session()
request_t = requests.Session()

def getScenes(url,type=''):
    if False:
        request_config = {"dlState": "any", "cardSize": "1", "lists": [], "isAvailable": None, "isAccessible": None,
                      "isWatched": None, "releaseMonth": "", "cast": [], "sites": [], "tags": [], "cuepoint": [],
                      "volume": 0, "sort": "release_desc", "offset": 0, "limit": 1}
    else:
        request_config={"dlState": "available", "cardSize": "1", "lists": [], "isAvailable": True, "isAccessible": True, "isHidden": False,
     "isWatched": None, "releaseMonth": "", "cast": [], "sites": [], "tags": [], "cuepoint": [], "attributes": [],
     "volume": 0, "sort": "release_desc", "offset": 0, "limit": 80}

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
        print('saving scene, %s %s' % (file_id,scene_id,))
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


def processtt():
    for f in filesList():
        if f['oshash']:
            ohash = f['oshash']
            if len(ohash) < 16:
                ohash = '0000000000000000'[len(ohash) - 16:] + ohash
            #            stashdb_match(ohash,f)
            tt_match(ohash, f)


def tt_match(ohash,f):
    try:
        response=request_t.post('https://timestamp.trade/hash_lookup?ohash='+ohash)
        if response.status_code==200:
            print('response: %s, %s'%(ohash,response.json(),))
            for r in response.json():
                for xid in r['xbvr-id']:
                    print(xid)
                    match(f['id'], xid)
#                    if xid in scenes:
#                        match(f,xid)
    except requests.exceptions.RequestException as err:
        print(err)
        time.sleep(15)
        return


def submit():
    submit_s = requests.Session()
    request_s = requests.Session()

    request_config={"dlState": "available", "cardSize": "1", "lists": [], "isAvailable": True, "isAccessible": True, "isHidden": False,
     "isWatched": None, "releaseMonth": "", "cast": [], "sites": [], "tags": [], "cuepoint": [], "attributes": [],
     "volume": 0, "sort": "release_desc", "offset": 0, "limit": 1}
    response = request_s.post(url + '/api/scene/list', json=request_config)


    if response.status_code == 200:
        print(response.json())
        total=response.json()['results']
        request_config['limit']=100
        request_config['offset']= 0
        while request_config['offset'] < total :
            response = request_s.post(url + '/api/scene/list', json=request_config)
            for s in response.json()['scenes']:
                if len(s['cuepoints']) > 0:
                    if s['id']==28185:
                        print(s)
                    for file in s['file']:
                        #if there is a hsp file get it from the api
                        if file['type']=='hsp':
                            hsp_req=request_s.get("%s/api/dms/file/%s"%(url,file['id'],))
                            if hsp_req.status_code==200:
                                s['hsp'] = base64.standard_b64encode(hsp_req.content).decode("ascii")
#                            filename=os.path.join(file['path'],file['filename'])
#                            with open(filename, 'rb') as fh:
#                                hsp = fh.read()
#                                s['hsp'] = base64.standard_b64encode(hsp).decode("ascii")

                    # I don't care about a lot of the fields in the scene, just remove them, I also don't care about the tag id and performer id in your instance only the name.
                    for k in ['id', 'file', '_score', 'history', 'favourite', 'is_watched', 'has_preview',
                              'is_scripted', 'last_opened', 'star_rating', 'is_available', 'is_multipart',
                              'needs_update', 'edits_applied', 'is_accessible', 'total_file_size',
                              'total_watch_time', 'created_at', 'watchlist','is_subscribed','is_hidden']:
                        s.pop(k)
                    s['tags'] = [{'name': x['name']} for x in s['tags']]
                    s['cast'] = [{'name': x['name']} for x in s['cast']]
                    for c in s['cuepoints']:
                        c.pop('id')
                        c.pop('rating')
                    print(s)
#                    submit_s.post('https://timestamp.trade/submit-xbvr2', json=s)
            request_config['offset']=request_config['offset']+request_config['limit']
            print('--'+str(request_config['offset']))
        submit_s.close()
        time.sleep(10)




def fetch_hsp(url,filesystem=False):
    if len(scenes) ==0:
        getScenes(url)
    response=request_t.get('https://timestamp.trade/hsp-index')
    if response.status_code==200:
        for h in response.json():
            for xid in h['xbvr_id']:
                if xid in scenes:
                    scene=scenes[xid]
                    print('saving hsp file for scene %s' % (scene,))
                    if filesystem:
                        if len(scene['file']) >0:
                            filename=os.path.join(scene['file'][0]['path'],scene['file'][0]['filename'][:-3]+'hsp')
                            print("Saving hsp to: %s" %(filename,))
                            with open(filename, "wb") as f:
                                f.write(base64.b64decode(h['hspb64']))
                                f.close()
                    else:
                        post_url='%s/heresphere/%s'% (url,scene['id'],)
                        print('posting hsp to xbvr api %s' %(post_url,))
                        request_s.post(post_url,json={' hsp':h['hspb64']},headers={'HereSphere-JSON-Version': "1"})


            True

def submit_hsp(filename,scene_id=None,ttid=None):
    if os.path.exists(filename):
        with open(filename, 'rb') as fh:
            hsp = fh.read()
            data={}
            data['hsp'] = base64.standard_b64encode(hsp).decode("ascii")



if __name__ == '__main__':
    print('syncing metadata')


    url = os.getenv('XBVR_HOST','http://127.0.0.1:9999')


#    stashbox_endpoint = os.getenv('STASHDB_ENDPOINT', 'https://stashdb.org/graphql')
#    api_key = os.getenv('STASHDB_KEY')

#    getScenes(url)
#    fetch_hsp(url)
    submit()
#    processtt()
#    submit_hsp(filename='/home/dns/src/xbvr-hsp/Babykxtten/Hot Sunbathing With BBC.hsp',scene_id='slr-22398',ttid='0a50c994-20be-4df7-9be3-0433b8fb5aa7')
#    process(api_key,stashbox_endpoint)

