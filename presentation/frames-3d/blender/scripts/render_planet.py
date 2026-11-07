"""Planet Daybreak look-test renderer and deterministic pixel anchor export."""
import bpy,json,math,time,sys,argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['preview','final','benchmark','morph'],default='preview'); p.add_argument('--engine',choices=['CYCLES','EEVEE'],default='CYCLES'); p.add_argument('--width',type=int,default=1920); p.add_argument('--samples',type=int,default=256); p.add_argument('--moments',nargs='+',default=['storm','problems','map','routes','dawn','outro']); args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s=bpy.context.scene; control=bpy.data.objects['Planet_Control']; cam=bpy.data.objects['Planet hero camera']; focus=bpy.data.objects['Photographic focus']; C=bpy.data.collections
if args.engine=='CYCLES':
    s.render.engine='CYCLES'; prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='METAL'
    if not any(d.use for d in prefs.devices): raise RuntimeError('Metal GPU required, refusing silent CPU fallback')
    s.cycles.device='GPU'; s.cycles.samples=args.samples; s.cycles.use_denoising=True; s.cycles.adaptive_threshold=.01
else:
    try: s.render.engine='BLENDER_EEVEE_NEXT'
    except TypeError: s.render.engine='BLENDER_EEVEE'
    if hasattr(s,'eevee'):
        for attr,value in [('taa_render_samples',128),('use_raytracing',True)]:
            if hasattr(s.eevee,attr): setattr(s.eevee,attr,value)
s.render.resolution_x=args.width; s.render.resolution_y=round(args.width*9/16); s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'; s.render.image_settings.color_depth='8'; s.render.use_persistent_data=True
MOMENTS={'storm':1.5,'problems':7.5,'map':9.8,'routes':14.,'dawn':23.,'outro':28.5}
TRACKS=ROOT/'tracks.json'
track_data=json.loads(TRACKS.read_text()) if TRACKS.exists() else {'schema':'daybreak.anchor-tracks.v1','width':1920,'height':1080,'origin':'top-left','units':'pixels','entries':{}}

def aim(loc,target,lens=50,fstop=2.8):
    cam.location=loc; target=Vector(target); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=lens; cam.data.shift_x=0; cam.data.shift_y=0; cam.data.dof.use_dof=True; cam.data.dof.aperture_fstop=fstop
    focus.location=target; cam.data.dof.focus_object=focus; s.camera=cam

def configure(moment,factor=None):
    t=MOMENTS.get(moment,0); f=0 if moment=='map' else 1 if factor is None else factor
    control['flat_to_planet']=f
    for name in ['village','depot','foliage','details','terrain']: C[name].hide_render=moment=='map'
    C['map_graphic'].hide_render=moment!='map'; C['storm'].hide_render=moment!='storm'; C['parked'].hide_render=moment not in ['storm','problems']; C['dispatch'].hide_render=moment!='dawn'; C['routes'].hide_render=moment not in ['routes','outro'] and factor is None
    key=bpy.data.objects['Warm museum studio key']; fill=bpy.data.objects['Cool silk fill']; rim=bpy.data.objects['Fine warm edge']; sun=bpy.data.objects['Daybreak moving sun']; sun.hide_render=moment!='dawn'; bpy.data.objects['Orange sunrise disc'].hide_render=moment!='dawn'
    for o in C['lights'].objects:
        if o.name.startswith('Problem spot'): o.hide_render=moment!='problems'
    s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.13
    key.data.energy=95; key.data.color=(1,.94,.83); fill.data.energy=28; rim.data.energy=50
    if moment=='storm':
        aim((-.48,-2.08,.65),(-.02,-.03,.06),50,1.4); focus.location=(-.06,-.25,.14)
        key.data.energy=25; key.data.color=(.48,.65,1); fill.data.energy=10; rim.data.energy=35; rim.data.color=(.62,.77,1)
        s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.045
    elif moment=='problems':
        aim((-.85,-2.02,.38),(-.04,-.05,.08),52,1.4); focus.location=(-.15,-.22,.10); key.data.energy=35
    elif moment=='map':
        aim((0,0,3.5),(0,0,0),42,32); cam.data.type='ORTHO'; cam.data.ortho_scale=1.16; cam.data.dof.use_dof=False
    elif moment=='routes':
        aim((-.35,-2.1,.65),(0,-.01,.04),52,1.4); focus.location=(-.06,-.25,.13); rim.data.color=(1,.83,.65)
    elif moment=='dawn':
        aim((-.08,-1.10,.34),(0,0,.09),56,2.8); focus.location=(-.07,-.25,.15)
        key.data.energy=24; fill.data.energy=12; rim.data.energy=0; s.world.node_tree.nodes['HDRI illumination'].inputs['Strength'].default_value=.035
        sun.data.energy=3.2; sun.rotation_euler=Vector((-.9,.25,-.4)).to_track_quat('-Z','Y').to_euler()
        bpy.data.objects['Orange sunrise disc'].location=(.30,.32,.23)
    elif moment=='outro':
        aim((-4.8,-8.2,4.4),(0,0,0),50,5.6); focus.location=(0,-.25,.2)
    else:
        aim((0,-2.7,2.9),(0,0,.05),50,32); cam.data.type='ORTHO'; cam.data.ortho_scale=3.52; cam.data.dof.use_dof=False
        key.data.energy=110; C['parked'].hide_render=False; C['routes'].hide_render=False
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type=='PARTICLE_SYSTEM': mod.show_render=f>.999
    for name in s.keys():
        if name.startswith('window_house_'):
            idx=int(name.rsplit('_',1)[1]); s[name]=2.0 if moment in ['storm','dawn'] else 0 if moment=='problems' and idx%3!=0 else .65
    for ob in C['parked'].objects:
        idx=int(ob.name.rsplit(' ',1)[-1])
        ob.hide_render=idx<1 if moment=='storm' else False if moment=='problems' else idx<3
    if moment in ['routes','outro','morph']: C['parked'].hide_render=False
    poses=json.loads(s['truck_pose_anchors']); pose='dispatch' if moment=='dawn' else 'storm' if moment=='storm' else 'parked' if moment in ['problems','map'] else 'routes'
    for i in range(3):
        data=poses[pose][i]; point=Vector(data['point']); cx,cy=data['center']
        point.x+=.22*math.sin(point.y*.4)+.06*math.sin(point.x); point.y+=.18*math.sin(data['point'][0]*.27); point.z-=.1
        cx2=cx+.22*math.sin(cy*.4)+.06*math.sin(cx); cy2=cy+.18*math.sin(cx*.27); radius=s['planet_radius']; latitude=s['latitude_offset']; scale=s['model_scale']; lon=cx2/radius; lat=cy2/radius+latitude
        n=Vector((math.cos(lat)*math.sin(lon),-math.cos(lat)*math.cos(lon),math.sin(lat))); ex=Vector((math.cos(lon),math.sin(lon),0)); ey=Vector((-math.sin(lat)*math.sin(lon),math.sin(lat)*math.cos(lon),math.cos(lat)))
        wrapped=n*(radius+point.z)+ex*(point.x-cx2)+ey*(point.y-cy2)
        anchor=bpy.data.objects['truck_'+str(i+1)]
        for axis in range(3):
            try: anchor.driver_remove('location',axis)
            except TypeError: pass
        anchor.location=(point*(1-f)+wrapped*f)*scale
    s.frame_set(round(t*30)+1); bpy.context.view_layer.update()

def anchors():
    deps=bpy.context.evaluated_depsgraph_get(); result={}
    for name in ['fallen_pole','meter','hot_roof','depot','unsure_house','truck_1','truck_2','truck_3']:
        ob=bpy.data.objects[name]; pos=ob.evaluated_get(deps).matrix_world.translation; co=world_to_camera_view(s,cam,pos); ray=pos-cam.location; dist=ray.length
        hit,point,normal,face,obj,matrix=s.ray_cast(deps,cam.location,ray.normalized(),distance=dist+.002)
        occluded=hit and (point-cam.location).length<dist-.009
        inside=0<=co.x<=1 and 0<=co.y<=1 and co.z>0
        result[name]={'x':round(co.x*1920,3),'y':round((1-co.y)*1080,3),'depth_m':round(co.z,6),'in_frame':inside,'occluded':bool(occluded),'visible':bool(inside and not occluded),'world_m':[round(v,7) for v in pos]}
    return result

def render(name,moment,factor=None):
    configure(moment,factor)
    folder='stills' if args.mode in ['final','morph'] else 'qa'
    suffix='' if folder=='stills' else '_'+args.engine.lower()
    path=ROOT/folder/(name+suffix+'.png'); s.render.filepath=str(path)
    start=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-start
    row={'engine':args.engine,'kind':args.mode,'name':name,'time_seconds':MOMENTS.get(moment),'factor':float(control['flat_to_planet']),'seconds':round(elapsed,3),'width':args.width,'height':s.render.resolution_y,'samples':args.samples if args.engine=='CYCLES' else 128,'file':str(path.relative_to(ROOT))}
    with (ROOT/'planet_timings.jsonl').open('a') as out: out.write(json.dumps(row)+'\n')
    if folder=='stills':
        track_data['entries'][name]={**row,'camera':{'matrix_world':[list(r) for r in cam.matrix_world],'lens_mm':cam.data.lens,'type':cam.data.type,'ortho_scale_m':cam.data.ortho_scale,'fstop':cam.data.dof.aperture_fstop,'focus_world_m':list(focus.location),'coordinate_system':'right-handed Blender Z-up, metres'},'anchors':anchors()}; TRACKS.write_text(json.dumps(track_data,indent=2)+'\n')
    print('PLANET_TIMING '+json.dumps(row),flush=True)
if args.mode=='morph':
    for factor,label in [(1,'1'),(.5,'05'),(0,'0')]: render('morph_'+label,'morph',factor)
else:
    if args.mode=='benchmark': render('benchmark_warmup','routes')
    for moment in args.moments: render('planet_'+moment,moment)
