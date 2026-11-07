"""Download only the selected public CC0 PBR maps and studio HDRI from Poly Haven's API."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[1]/'assets'; ROOT.mkdir(exist_ok=True)
UA={'User-Agent':'Daybreak miniature film look test, local Blender asset download'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=90).read()
assets=['clay_roof_tiles_02','white_plaster_rough_01','gravel_road','asphalt_02','bark_brown_02','european_walnut_veneer_04','grass_ground']
manifest=[]; jobs=[]
for aid in assets+['studio_small_03']:
    data=json.loads(get('https://api.polyhaven.com/files/'+aid)); (ROOT/(aid+'_files.json')).write_text(json.dumps(data,indent=2))
    item={'name':aid,'asset_url':'https://polyhaven.com/a/'+aid,'api_url':'https://api.polyhaven.com/files/'+aid,'license':'CC0-1.0','license_url':'https://polyhaven.com/license','files':{}}
    for kind in (['hdri'] if aid=='studio_small_03' else ['Diffuse','Rough','nor_gl','Displacement']):
        if kind not in data: continue
        resolution='4k' if kind=='hdri' else '1k' if kind=='Displacement' else '2k'
        if resolution not in data[kind]: resolution=list(data[kind])[0]
        fmt='hdr' if kind=='hdri' else 'jpg'; record=data[kind][resolution][fmt]
        target=ROOT/record['url'].split('/')[-1]
        entry={'url':record['url'],'local':target.name,'md5':record.get('md5'),'resolution':resolution,'bytes':record['size']}
        item['files'][kind]=entry; jobs.append((target,entry))
    manifest.append(item)
def download(job):
    path,entry=job
    if not path.exists() or path.stat().st_size!=entry['bytes']:
        content=get(entry['url']); path.write_bytes(content)
    if entry['md5']: assert hashlib.md5(path.read_bytes()).hexdigest()==entry['md5'],path
    return path.name
with ThreadPoolExecutor(max_workers=4) as pool:
    for name in pool.map(download,jobs): print('ASSET_OK',name,flush=True)
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Complete:',len(manifest),'assets;',len(jobs),'files',flush=True)
