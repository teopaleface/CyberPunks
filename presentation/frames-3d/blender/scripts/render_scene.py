"""Cycles Metal stills / preview / timed motion. See README for exact commands."""
import bpy, sys, time, json, math, argparse, statistics
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['preview','stills','motion','benchmark'],default='stills'); p.add_argument('--beats',nargs='+',default=['storm','where','problems','map','dawn']); p.add_argument('--samples',type=int); p.add_argument('--width',type=int,default=1920); p.add_argument('--start',type=int,default=1); p.add_argument('--end',type=int,default=180)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.get_devices()
for d in prefs.devices: d.use=d.type=='METAL'
if not any(d.use for d in prefs.devices): raise RuntimeError('Metal GPU unavailable; refusing silent CPU fallback.')
print('METAL_DEVICES '+str([(d.name,d.type,d.use) for d in prefs.devices]),flush=True)
scene.render.engine='CYCLES'; scene.cycles.device='GPU'; scene.cycles.use_denoising=True
scene.cycles.samples=args.samples or (24 if args.mode=='preview' else 48 if args.mode in ['motion','benchmark'] else 256)
scene.render.resolution_x=args.width; scene.render.resolution_y=round(args.width*9/16); scene.render.resolution_percentage=100
scene.render.use_persistent_data=True
COL=bpy.data.collections
paths=json.loads(scene['route_paths']); pins=json.loads(scene['pin_specs'])
def visible(beat):
    hidden={'storm','parked','dispatch','routes','problems'}
    show={'storm':['storm'],'where':['parked'],'dawn':['dispatch'],'map':['routes'],'problems':['problems']}[beat]
    for name in hidden: COL[name].hide_render=name not in show
    for name in ['village','depot']: COL[name].hide_render=beat=='problems' or name=='village' and beat=='where'
    for name in ['storm','where','problems','map','dawn']: COL['light_'+name].hide_render=name!=beat
    scene.camera=bpy.data.objects[beat]
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    scene.view_settings.exposure=-.5

def reset_routes():
    for i in range(3):
        bpy.data.objects['Route %d | drawn by bevel_factor_end'%i].data.bevel_factor_end=1
        t=bpy.data.objects['Moving route truck %d'%i]; t.location=paths[i][0]; t.rotation_euler.z=0
    for name,i,f in pins:
        bpy.data.objects[name].location.z=0; bpy.data.objects[name].scale=(1,.72,1)
        bpy.data.objects['House tether '+name].data.bevel_factor_end=1
def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def at(points,t):
    ps=[Vector(x) for x in points]; ls=[(b-a).length for a,b in zip(ps,ps[1:])]; total=sum(ls); dist=max(0,min(1,t))*total
    for a,b,l in zip(ps,ps[1:],ls):
        if dist<=l: return a.lerp(b,dist/l),(b-a)
        dist-=l
    return ps[-1],ps[-1]-ps[-2]
def motion(frame):
    t=(frame-1)/179; e=ease(t)
    a=bpy.data.objects['where']; b=bpy.data.objects['map']; cam=bpy.data.objects.get('motion_camera')
    if cam is None:
        cam=bpy.data.objects.new('motion_camera',a.data.copy()); COL['cameras'].objects.link(cam)
    cam.location=a.location.lerp(b.location,e)
    cam.rotation_mode='QUATERNION'
    zoom=1-(1-e)**1.5
    focus=Vector((-15,-2.9,.8)).lerp(Vector((0,0,0)),zoom)
    cam.rotation_quaternion=(focus-cam.location).to_track_quat('-Z','Y')
    cam.data.ortho_scale=(1-zoom)*a.data.ortho_scale+zoom*b.data.ortho_scale
    cam.data.shift_y=(1-e)*a.data.shift_y+e*b.data.shift_y; cam.data.shift_x=0
    cam.data.dof.use_dof=False; scene.camera=cam
    for i in range(3):
        progress=ease((t-.08-i*.035)/.82)
        bpy.data.objects['Route %d | drawn by bevel_factor_end'%i].data.bevel_factor_end=max(.00001,progress)
        truck=bpy.data.objects['Moving route truck %d'%i]
        travel=max(0,progress*.78-.015)
        pos,_=at(paths[i],travel); ahead,_=at(paths[i],min(1,travel+.009)); behind,_=at(paths[i],max(0,travel-.009)); direction=ahead-behind
        truck.location=pos; truck.rotation_euler.z=math.atan2(direction.y,direction.x)
    for name,i,f in pins:
        o=bpy.data.objects[name] # Invert smoothstep for the exact route-arrival time.
        lo,hi=0.,1.
        for _ in range(20):
            mid=(lo+hi)/2
            if ease(mid)<f: lo=mid
            else: hi=mid
        arrival=.08+i*.035+.82*(lo+hi)/2
        q=ease((t-arrival)/.075); o.location.z=(1-q)*2.5; s=max(.0001,q); o.scale=(s,s*.72,s)
        bpy.data.objects['House tether '+name].data.bevel_factor_end=max(.00001,q)
    scene.frame_set(frame)

def render(path,kind,beat,frame=None):
    scene.render.filepath=str(path); t=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-t
    data={'kind':kind,'beat':beat,'frame':frame,'seconds':round(elapsed,3),'samples':scene.cycles.samples,'width':scene.render.resolution_x,'height':scene.render.resolution_y,'device':'Apple M5 Max Metal GPU','file':str(path.relative_to(ROOT))}
    with (ROOT/'timings.jsonl').open('a') as f: f.write(json.dumps(data)+'\n')
    print('DAYBREAK_TIMING '+json.dumps(data),flush=True)

if args.mode in ['preview','stills']:
    for beat in args.beats:
        visible(beat); reset_routes()
        out=ROOT/('qa' if args.mode=='preview' else 'stills')/(beat+'.png')
        render(out,args.mode,beat)
else:
    visible('map'); reset_routes()
    # The camera starts at the depot; three active trucks replace the five parked trucks.
    frames=[1,90,180] if args.mode=='benchmark' else range(args.start,args.end+1)
    for frame in frames:
        motion(frame); out=(ROOT/'qa'/('motion_%04d.png'%frame)) if args.mode=='benchmark' else ROOT/'motion'/'frames'/('%04d.png'%frame)
        render(out,args.mode,'map',frame)
