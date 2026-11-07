"""Validate delivered PNGs, write compositor manifests, and assemble navy contact."""
from pathlib import Path
from PIL import Image, ImageChops
import json, time
ROOT=Path(__file__).resolve().parent
NAMES=['truck','meter','pole','solar','hardhat','pin_orange','pin_cyan','pin_blue','cloud']

def inspect(path,size):
    with Image.open(path) as im:
        im.load();assert im.size==(size,size),(path,im.size);assert im.mode=='RGBA',(path,im.mode)
        a=im.getchannel('A');assert a.getextrema()==(0,255),(path,a.getextrema())
        bb=a.point(lambda x:255 if x>8 else 0).getbbox();assert bb,(path,'empty')
        assert bb[0]>0 and bb[1]>0 and bb[2]<size and bb[3]<size,(path,'clipped',bb)
        return {'alpha_bbox_px':list(bb),'min_padding_px':min(bb[0],bb[1],size-bb[2],size-bb[3]),'bytes':path.stat().st_size}

def main():
    contact=Image.new('RGB',(2400,2400),'#000F1E');manifests=[];qa={};total=0
    for index,name in enumerate(NAMES):
        folder=ROOT/name;hero=inspect(folder/'hero.png',1600);q={'hero':hero,'sequences':{}}
        with Image.open(folder/'hero.png') as im:
            thumb=im.resize((800,800),Image.Resampling.LANCZOS);contact.paste(thumb,(index%3*800,index//3*800),thumb.getchannel('A'))
        m={'schema_version':1,'name':name,'engine':'Blender 5.2.1 LTS / Cycles / Metal','color_management':{'view':'AgX','look':'Medium High Contrast','exposure':-.25,'output':'sRGB display-referred'},'camera':{'projection':'perspective','focal_length_mm':70,'model_scale':1/87,'hero_aperture_fstop':32 if name=='truck' else 64},'alpha':'straight','background':'transparent','pivot_3d':[0,0,0],'fps':30,'hero':{'path':'hero.png','size_px':[1600,1600],'pivot_px':[800,800],'root_rotation_euler_xyz_degrees':[0,0,0],**hero},'sequences':{},'source':'scene.blend','external_assets':[]}
        for mode,count in [('spin',72),('tumble',48)]:
            files=sorted((folder/mode).glob('*.png'));expected=[f'{f:04d}.png' for f in range(count)]
            assert [p.name for p in files]==expected,(name,mode,len(files))
            frames=[inspect(p,1024) for p in files];total+=len(frames)
            entry={'path_pattern':mode+'/%04d.png','first_frame':0,'last_frame':count-1,'frame_count':count,'size_px':[1024,1024],'pivot_px':[512,512],'duration_seconds':count/30,'hero_angle_frame':0 if mode=='spin' else 47,'loop':mode=='spin','motion_blur':{'enabled':mode=='tumble','shutter_frames':.72 if mode=='tumble' else 0,'position':'CENTER'},'camera_framing':'Fixed sphere-safe framing' if mode=='spin' else 'Sphere-safe start, eased settle to hero framing over frames 28-47'}
            m['sequences'][mode]=entry
            q['sequences'][mode]={'frame_count':count,'minimum_padding_px':min(f['min_padding_px'] for f in frames),'total_bytes':sum(f['bytes'] for f in frames)}
        (folder/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');manifests.append({'name':name,'manifest':name+'/manifest.json'});qa[name]=q
    contact.save(ROOT/'contact_navy.jpg',quality=96,subsampling=0)
    (ROOT/'manifest.json').write_text(json.dumps({'schema_version':1,'objects':manifests,'contact_sheet':'contact_navy.jpg','contact_order':'Left to right, top to bottom','navy':'#000F1E','total_sequence_frames':total,'total_hero_images':9},indent=2)+'\n')
    (ROOT/'validation.json').write_text(json.dumps({'all_images_decoded':True,'all_images_rgba':True,'all_images_have_transparency':True,'all_images_unclipped_at_alpha_gt_8':True,'object_count':len(NAMES),'sequence_frame_count':total,'objects':qa},indent=2)+'\n')
    print('VALIDATED',len(NAMES),'objects;',total,'sequence frames;',9,'heroes')
if __name__=='__main__':main()
