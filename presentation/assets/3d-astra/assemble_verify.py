"""Assemble exact PNG frames, validate alpha/framing, and make review previews.
Needs Pillow. Run with --heroes-only during art direction; no files outside HERE.
"""
from pathlib import Path
import argparse, json, statistics
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

HERE=Path(__file__).resolve().parent
NAMES=['meter','transformer','solar','storm','helmet']
LABELS=['Contor inteligent','Transformator','Panou solar','Furtună','Cască de protecție']
parser=argparse.ArgumentParser(); parser.add_argument('--heroes-only', action='store_true'); args=parser.parse_args()
try: font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',25)
except OSError: font=ImageFont.load_default(size=25)
report={'files':[], 'objects':{}, 'failures':[]}

def check(path,size,edge=True):
    if not path.exists(): raise AssertionError(f'Missing {path.name}')
    im=Image.open(path); im.load()
    assert im.size==size, (path,im.size,size)
    assert im.mode=='RGBA', (path,im.mode)
    a=im.getchannel('A'); w,h=im.size
    corners=[a.getpixel(pt) for pt in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]]
    assert corners==[0]*4,(path,corners)
    bbox=a.getbbox(); assert bbox is not None,(path,'empty')
    assert a.getextrema()==(0,255),(path,'missing real opaque/transparent pixels')
    margin=min(bbox[0],bbox[1],w-bbox[2],h-bbox[3])
    if edge: assert margin>=4,(path,'silhouette too near frame edge',bbox)
    report['files'].append({'path':str(path.relative_to(HERE)),'size':list(size),'mode':im.mode,'corner_alpha':corners,'alpha_bbox':list(bbox),'minimum_margin_px':margin})
    return im

contact=Image.new('RGB',(2560,586),'white')
for index,(name,label) in enumerate(zip(NAMES,LABELS)):
    hero=check(HERE/(name+'_hero.png'),(1024,1024))
    small=hero.resize((512,512),Image.Resampling.LANCZOS)
    contact.paste(small,(index*512,10),small)
    draw=ImageDraw.Draw(contact); draw.text((index*512+256,550),label,font=font,fill='#0B1622',anchor='mm')
    if args.heroes_only: continue
    frames=[check(HERE/(name+'_spin')/f'{i:04d}.png',(512,512)) for i in range(30)]
    assert len(list((HERE/(name+'_spin')).glob('*.png')))==30
    sheet=Image.new('RGBA',(3072,2560),(0,0,0,0))
    for i,im in enumerate(frames): sheet.paste(im,((i%6)*512,(i//6)*512))
    sheet_path=HERE/(name+'_spin_sheet.png'); sheet.save(sheet_path,compress_level=6)
    check(sheet_path,(3072,2560))
    for i,im in enumerate(frames):
        extracted=sheet.crop(((i%6)*512,(i//6)*512,(i%6+1)*512,(i//6+1)*512))
        assert ImageChops.difference(im,extracted).getbbox() is None
    # Keep exactly the rendered frames; the terminal pose is held in the preview only.
    frames[0].save(HERE/(name+'_preview.webp'),save_all=True,append_images=frames[1:]+[frames[-1]],duration=[33]*30+[700],loop=0,lossless=True,method=4)
    smallhero=hero.resize((512,512),Image.Resampling.LANCZOS)
    # Compare premultiplied-looking composites on white to avoid meaningless RGB at alpha zero.
    def white(im):
        out=Image.new('RGBA',im.size,'white'); out.alpha_composite(im); return out.convert('RGB')
    delta=ImageStat.Stat(ImageChops.difference(white(smallhero),white(frames[-1]))).mean
    assert max(delta)<5.0,(name,'hero and terminal pose differ',delta)
    paths=[x for x in report['files'] if x['path'].startswith(name+'_spin/')]
    timing=json.loads((HERE/(name+'_timing_spin.json')).read_text())['frames'] if (HERE/(name+'_timing_spin.json')).exists() else json.loads((HERE/(name+'_timing_all.json')).read_text())['frames']
    spin_times=[x['seconds'] for x in timing if x['size']==512]
    report['objects'][name]={'frame_count':30,'sheet_exact_copy':True,'minimum_spin_margin_px':min(x['minimum_margin_px'] for x in paths),'hero_end_pose_mean_rgb_difference':delta,'spin_mean_seconds':statistics.mean(spin_times),'spin_median_seconds':statistics.median(spin_times),'spin_min_seconds':min(spin_times),'spin_max_seconds':max(spin_times)}
contact.save(HERE/'contact_white.png')
assert Image.open(HERE/'contact_white.png').size==(2560,586)
if not args.heroes_only:
    # Combined white preview for quick review without a compositing application.
    previews=[]
    for frame in range(30):
        preview=Image.new('RGB',(1600,364),'white'); draw=ImageDraw.Draw(preview)
        for i,(name,label) in enumerate(zip(NAMES,LABELS)):
            im=Image.open(HERE/(name+'_spin')/f'{frame:04d}.png').resize((320,320),Image.Resampling.LANCZOS)
            preview.paste(im,(320*i,0),im); draw.text((320*i+160,341),label,font=font,fill='#0B1622',anchor='mm')
        previews.append(preview)
    previews[0].save(HERE/'turntables_white.webp',save_all=True,append_images=previews[1:]+[previews[-1]],duration=[40]*30+[850],loop=0,lossless=True,method=4)
    report['verified_png_count']=len(report['files'])
    report['status']='PASS'
    (HERE/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'PNG_count':report['verified_png_count'],'objects':report['objects']},indent=2))
else: print('Hero contact sheet saved:',HERE/'contact_white.png')
