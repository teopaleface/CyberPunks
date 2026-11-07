import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent
names=['truck','meter','pole','solar','hardhat','pin_orange','pin_cyan','pin_blue','cloud'];out={}
for name in names:
    bpy.ops.wm.open_mainfile(filepath=str(R/name/'scene.blend'))
    s=bpy.context.scene;c=s.camera;r=bpy.data.objects['PROP_PIVOT']
    assert s.render.engine=='CYCLES' and s.cycles.device=='GPU'
    assert c.data.type=='PERSP' and c.data.lens==70
    assert all(abs(v-1/87)<1e-6 for v in r.scale)
    assert not any(o.type=='FONT' for o in s.objects)
    out[name]={'camera':c.data.type,'lens_mm':c.data.lens,'hero_fstop':c.data.dof.aperture_fstop,'hero_focus_distance_m':c.data.dof.focus_distance,'hero_camera_distance_m':s['hero_camera_distance'],'spin_camera_distance_m':s['spin_camera_distance'],'motion_blur_position':s.render.motion_blur_position,'cycles_gpu':s.cycles.device,'gpu_denoising':s.cycles.denoising_use_gpu,'root_scale':list(r.scale),'text_objects':0}
(R/'source_validation.json').write_text(json.dumps(out,indent=2))
print('SOURCE_VALIDATED',len(out),'perspective macro scenes',flush=True)
