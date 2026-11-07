import bpy,time,json
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parent
for name in ['truck','meter']:
    bpy.ops.wm.open_mainfile(filepath=str(R/name/'scene.blend'))
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
    for d in p.devices:d.use=d.type=='METAL'
    s=bpy.context.scene;c=s.camera;direction=c.location.normalized();focus=Vector((-1,-.65,-.1)) if name=='truck' else Vector((0,-.37,.25))
    c.data.dof.focus_distance=c.location.length-direction.dot(focus)/87;c.data.dof.aperture_fstop=32 if name=='truck' else 64
    bpy.ops.wm.save_as_mainfile(filepath=str(R/name/'scene.blend'))
    s.render.filepath=str(R/name/'hero.png');t=time.perf_counter();bpy.ops.render.render(write_still=True);elapsed=time.perf_counter()-t
    data=json.loads((R/'timings.json').read_text());data[name]['hero_seconds']=round(elapsed,3);(R/'timings.json').write_text(json.dumps(data,indent=2))
    print('OBJECTS_HERO_DONE',name,elapsed,flush=True)
