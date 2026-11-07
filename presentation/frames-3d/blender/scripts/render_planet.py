"""Cycles/EEVEE look-test renderer from the parent's exact 900-frame camera path."""
import bpy,json,math,time,sys,argparse,hashlib,datetime
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['preview','final','benchmark','morph'],default='preview'); p.add_argument('--engine',choices=['CYCLES','EEVEE'],default='CYCLES'); p.add_argument('--width',type=int,default=1920); p.add_argument('--samples',type=int,default=256); p.add_argument('--moments',nargs='+',default=['storm','problems','map','routes','dawn','outro']); p.add_argument('--camera-path',default=str(ROOT/'assets'/'camera_path.json')); p.add_argument('--hero',action='store_true'); args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s=bpy.context.scene; control=bpy.data.objects['Planet_Control']; cam=bpy.data.objects['Planet hero camera']; focus=bpy.data.objects['Photographic focus']; C=bpy.data.collections
exec(compile((ROOT/'scripts'/'prepare_damage.py').read_text(),str(ROOT/'scripts'/'prepare_damage.py'),'exec'),globals())
SCENE_HASH=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
PATH=json.loads(Path(args.camera_path).read_text()); assert len(PATH['frames'])==900
RP=float(s['model_scale'])*float(s['planet_radius'])
if args.engine=='CYCLES':
    s.render.engine='CYCLES'; prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='METAL'
    if not any(d.use for d in prefs.devices): raise RuntimeError('Metal GPU required; no silent CPU fallback')
    s.cycles.device='GPU'; s.cycles.samples=args.samples; s.cycles.use_denoising=True; s.cycles.denoiser='OPENIMAGEDENOISE'; s.cycles.adaptive_threshold=.015; s.cycles.max_bounces=8
else:
    try: s.render.engine='BLENDER_EEVEE_NEXT'
    except TypeError: s.render.engine='BLENDER_EEVEE'
    s.eevee.taa_render_samples=128; s.eevee.use_raytracing=True
s.render.resolution_x=args.width; s.render.resolution_y=round(args.width*9/16); s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'; s.render.image_settings.color_depth='8'; s.render.use_persistent_data=True
MOMENTS={'storm':1.5,'problems':7.5,'map':9.8,'routes':14.,'dawn':23.,'outro':28.5}
TRACKS=ROOT/'tracks.json'; track_data=json.loads(TRACKS.read_text()) if TRACKS.exists() else {'schema':'daybreak.anchor-tracks.v2','width':1920,'height':1080,'origin':'top-left','units':'pixels','entries':{}}

exec(compile((ROOT/'scripts'/'camera_io.py').read_text(),str(ROOT/'scripts'/'camera_io.py'),'exec'),globals())
def three_to_blender(p,scale=RP): return convert(p,scale)
def orient_camera(position,target): return look_at(cam,position,target)
def import_camera(entry): return apply_camera(s,cam,entry,RP,focus)

def set_anchor_raw(name,point,center):
    scale=s['model_scale']; R=s['planet_radius']; x,y,z=point; cx,cy=center
    x0=x; x+=.10*math.sin(y*.4); y+=.10*math.sin(x0*.27); z-=.10
    ccx=cx+.10*math.sin(cy*.4); ccy=cy+.10*math.sin(cx*.27)
    obj=bpy.data.objects[name]
    obj.data.attributes['flat_position'].data[0].vector=(x*scale,y*scale,(R+z)*scale)
    obj.data.attributes['actor_center'].data[0].vector=(ccx*scale,ccy*scale,1)
    obj.data.update(); obj.update_tag()

def configure(moment,factor=None):
    t=MOMENTS.get(moment,14.); index=min(899,round(t*30)); entry=PATH['frames'][index]
    f=float(entry['f']) if factor is None else factor
    if abs(float(control['flat_to_planet'])-f)>1e-7:
        control['flat_to_planet']=f; control.update_tag(refresh={'OBJECT'})
    for name in ['village','depot','foliage','details','terrain']: C[name].hide_render=False
    C['map_graphic'].hide_render=True
    C['damage'].hide_render=moment in ['dawn','outro']
    C['storm'].hide_render=moment!='storm'; C['parked'].hide_render=moment not in ['storm','problems','map','routes','outro','morph']; C['dispatch'].hide_render=moment!='dawn'; C['routes'].hide_render=moment not in ['routes','outro','morph']
    key=bpy.data.objects['Warm museum studio key']; fill=bpy.data.objects['Cool silk fill']; rim=bpy.data.objects['Fine warm edge']; sun=bpy.data.objects['Daybreak moving sun']
    sun.hide_render=moment not in ['dawn','outro']; bpy.data.objects['Orange sunrise disc'].hide_render=True
    for obj in C['lights'].objects:
        if obj.name.startswith('Problem spot'): obj.hide_render=moment!='problems'
    s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.12
    key.data.energy=105; key.data.color=(1,.92,.78); fill.data.energy=26; fill.data.color=(.61,.77,1); rim.data.energy=48; rim.data.color=(1,.83,.62)
    if moment in ['storm','problems']:
        key.data.energy=42 if moment=='storm' else 55; key.data.color=(.65,.78,1); fill.data.energy=12; rim.data.energy=30; rim.data.color=(.67,.8,1); s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.055
    if moment in ['dawn','outro']:
        key.data.energy=38; key.data.color=(1,.73,.43); fill.data.energy=28; fill.data.color=(1,.88,.64); rim.data.energy=0; s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.045
        direction=three_to_blender(entry['sun']['position']).normalized(); sun.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler(); sun.data.energy=3.5; sun.data.color=(1,.62,.30)
    if factor is None: import_camera(entry)
    else:
        orient_camera((0,-2.4,3.2),(0,0,RP*.65)); cam.data.type='ORTHO'; cam.data.ortho_scale=3.15; cam.data.shift_x=cam.data.shift_y=0; cam.data.dof.use_dof=False
    if args.hero:
        orient_camera((-2.05,-3.32,3.27),(0,0,RP*.12)); cam.data.type='PERSP'; cam.data.lens=85; cam.data.sensor_width=36; cam.data.shift_x=cam.data.shift_y=0; cam.data.dof.use_dof=True; cam.data.dof.aperture_fstop=2; focus.location=(0,-.08,RP+.01)
    if moment=='dawn' and factor is None:
        bpy.context.view_layer.update(); focus.location=evaluated_anchor('hot_roof',bpy.context.evaluated_depsgraph_get()); cam.data.dof.aperture_fstop=9
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type=='PARTICLE_SYSTEM': mod.show_render=f>.999 and obj.name!='Planet_storm_cloud'
    for name in list(s.keys()):
        if name.startswith('window_house_'):
            idx=int(name.rsplit('_',1)[1]); value=1.5 if moment in ['storm','dawn'] else 0 if moment=='problems' and idx%3!=0 else .35
            if s[name]!=value: s[name]=value
    for obj in C['parked'].objects:
        idx=int(obj.name.rsplit(' ',1)[-1]); obj.hide_render=idx<1 if moment=='storm' else False if moment in ['problems','map'] else idx<3
    poses=json.loads(s['truck_pose_anchors']); pose='dispatch' if moment=='dawn' else 'storm' if moment=='storm' else 'parked' if moment in ['problems','map'] else 'routes'
    for i in range(3): set_anchor_raw('truck_'+str(i+1),poses[pose][i]['point'],poses[pose][i]['center'])
    # ray_cast and render must see the same geometry; render-hidden flat overlays are never occluders.
    for coll in C:
        if coll.name!='Collection': coll.hide_viewport=coll.hide_render
    for obj in bpy.data.objects:
        obj.hide_viewport=obj.hide_render
    s.frame_set(index+1); bpy.context.view_layer.update()
    return entry,index

def evaluated_anchor(name,deps):
    obj=bpy.data.objects[name].evaluated_get(deps)
    return obj.matrix_world@obj.data.vertices[0].co

def anchors():
    deps=bpy.context.evaluated_depsgraph_get(); result={}
    for name in ['fallen_pole','meter','hot_roof','depot','unsure_house','truck_1','truck_2','truck_3']:
        pos=evaluated_anchor(name,deps); co=world_to_camera_view(s,cam,pos); ray=pos-cam.location; dist=ray.length
        hit,point,normal,face,obj,matrix=s.ray_cast(deps,cam.location,ray.normalized(),distance=dist+.002)
        occluded=hit and (point-cam.location).length<dist-.006
        inside=0<=co.x<=1 and 0<=co.y<=1 and co.z>0
        result[name]={'x':round(co.x*1920,3),'y':round((1-co.y)*1080,3),'depth_m':round(co.z,6),'in_frame':bool(inside),'occluded':bool(occluded),'visible':bool(inside and not occluded),'world_m':[round(v,7) for v in pos]}
    return result

def render(name,moment,factor=None):
    preparation_start=time.perf_counter(); entry,index=configure(moment,factor); preparation=time.perf_counter()-preparation_start
    folder='stills' if args.mode in ['final','morph'] else 'qa'; suffix='' if folder=='stills' else '_'+args.engine.lower()
    path=ROOT/folder/(name+suffix+'.png'); s.render.filepath=str(path)
    start=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-start
    row={'engine':args.engine,'kind':args.mode,'name':name,'time_seconds':MOMENTS.get(moment),'source_frame':index,'factor':float(control['flat_to_planet']),'seconds':round(elapsed+preparation,3),'render_seconds':round(elapsed,3),'prepare_seconds':round(preparation,3),'width':args.width,'height':s.render.resolution_y,'samples':args.samples if args.engine=='CYCLES' else 128,'file':str(path.relative_to(ROOT)),'camera_source':'camera_path.json' if factor is None and not args.hero else 'fixed morph proof' if factor is not None else 'hero detail camera'}
    row['scene_sha256']=SCENE_HASH; row['measured_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (ROOT/'planet_timings.jsonl').open('a') as out: out.write(json.dumps(row)+'\n')
    if folder=='stills':
        track_data['entries'][name]={**row,'camera':{'matrix_world':[list(r) for r in cam.matrix_world],'lens_mm':cam.data.lens,'sensor_width_mm':cam.data.sensor_width,'shift':[cam.data.shift_x,cam.data.shift_y],'type':cam.data.type,'fstop':cam.data.dof.aperture_fstop,'focus_world_m':list(focus.location),'coordinate_system':'Blender Z-up metres; Three.js (x,y,z) becomes (x,-z,y) times planet radius'},'anchors':anchors()}; TRACKS.write_text(json.dumps(track_data,indent=2)+'\n')
    print('PLANET_TIMING '+json.dumps(row),flush=True)
if args.mode=='morph':
    for factor,label in [(1,'1'),(.5,'05'),(0,'0')]: render('morph_'+label,'morph',factor)
else:
    if args.mode=='benchmark': render('benchmark_warmup','routes')
    for moment in args.moments: render('planet_'+moment+('_hero' if args.hero else ''),moment)
