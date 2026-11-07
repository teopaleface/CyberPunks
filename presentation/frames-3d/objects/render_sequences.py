"""Resume-safe Cycles renderer. One Blender process, shared GPU, no parallel renders."""
import bpy, math, sys, time, json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
NAMES=['truck','meter','pole','solar','hardhat','pin_orange','pin_cyan','pin_blue','cloud']
names=args or NAMES
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
print('OBJECTS_RENDER_DEVICES',[(d.name,d.type,d.use) for d in prefs.devices],flush=True)
for name in names:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/name/'scene.blend'))
    s=bpy.context.scene;r=bpy.data.objects['PROP_PIVOT'];cam=s.camera
    s.render.resolution_x=1024;s.render.resolution_y=1024
    s.cycles.samples=24;s.cycles.adaptive_threshold=.065;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE';s.cycles.denoising_use_gpu=True
    s.render.use_persistent_data=True
    view_direction=cam.location.normalized();cam.location=view_direction*s['spin_camera_distance'];cam.data.dof.use_dof=False
    # Opaque prop motion blur produces real RGBA edge coverage in the shutter interval.
    for mode,count in [('spin',72),('tumble',48)]:
        r.animation_data_clear();cam.animation_data_clear();cam.data.animation_data_clear();r.rotation_mode='XYZ'
        cam.location=view_direction*s['spin_camera_distance']
        if mode=='spin':
            for f,a in [(0,0),(72,2*math.pi)]:r.rotation_euler=(0,0,a);r.keyframe_insert('rotation_euler',frame=f)
            for fc in r.animation_data.action.layers[0].strips[0].channelbag(r.animation_data.action_slot).fcurves:
                for k in fc.keyframe_points:k.interpolation='LINEAR'
            s.render.use_motion_blur=False
        else:
            for f in range(-1,50):
                t=max(0,min(1,f/47));q=(1-t)**2
                r.rotation_euler=(2.4*math.pi*q,1.6*math.pi*q,2.7*math.pi*q);r.keyframe_insert('rotation_euler',frame=f)
            s.render.use_motion_blur=True;s.render.motion_blur_shutter=.72
            # Keep final composition identical to the hero, with an eased camera settle.
            for f in [-1,0,28,47,49]:
                if f<=28:distance=s['spin_camera_distance']
                else:distance=s['hero_camera_distance']
                cam.location=view_direction*distance;cam.keyframe_insert('location',frame=f)
        out=ROOT/name/mode;out.mkdir(exist_ok=True);s.frame_start=0;s.frame_end=count-1
        durations=[];started=time.perf_counter();rendered=0
        for f in range(count):
            dst=out/f'{f:04d}.png'
            force_objects=set(filter(None,os.environ.get('OBJECTS_FORCE_OBJECTS','').split(',')))
            if dst.exists() and name not in force_objects and not(name=='truck' and mode=='spin' and f<int(os.environ.get('OBJECTS_REDO_TRUCK_PREFIX','0'))):continue
            s.frame_set(f);s.render.filepath=str(dst);t=time.perf_counter();bpy.ops.render.render(write_still=True);durations.append(time.perf_counter()-t);rendered+=1
            print('OBJECTS_FRAME',name,mode,f,round(durations[-1],3),flush=True)
        timings=json.loads((ROOT/'timings.json').read_text())
        prior=timings.setdefault(name,{}).get(mode,{})
        timings[name][mode]={'frames':count,'rendered_this_run':rendered,'wall_seconds_this_run':round(time.perf_counter()-started,3),'sum_render_seconds_this_run':round(sum(durations),3),'samples':24,'motion_blur':mode=='tumble','shutter_frames':.72 if mode=='tumble' else 0,'previous_run':prior or None}
        (ROOT/'timings.json').write_text(json.dumps(timings,indent=2))
    print('OBJECTS_SEQUENCES_DONE',name,flush=True)
