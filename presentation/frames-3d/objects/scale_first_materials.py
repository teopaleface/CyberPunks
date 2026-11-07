"""One-time correction of the first two macro drafts; authoring script now does this."""
import bpy,sys,time,json
from pathlib import Path
R=Path(__file__).resolve().parent
for name in ['truck','meter']:
    bpy.ops.wm.open_mainfile(filepath=str(R/name/'scene.blend'))
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
    for d in p.devices:d.use=d.type=='METAL'
    for m in bpy.data.materials:
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type=='BUMP':n.inputs['Distance'].default_value/=87
                if n.type=='BSDF_PRINCIPLED':n.inputs['Subsurface Scale'].default_value/=87
    bpy.ops.wm.save_as_mainfile(filepath=str(R/name/'scene.blend'))
    s=bpy.context.scene;s.render.filepath=str(R/name/'hero.png');t=time.perf_counter();bpy.ops.render.render(write_still=True);elapsed=time.perf_counter()-t
    data=json.loads((R/'timings.json').read_text());data[name]['hero_seconds']=round(elapsed,3);(R/'timings.json').write_text(json.dumps(data,indent=2))
    print('OBJECTS_HERO_DONE',name,elapsed,flush=True)
