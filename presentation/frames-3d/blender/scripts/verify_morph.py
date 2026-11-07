import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
exec(compile((ROOT/'scripts'/'planet_geometry.py').read_text(),str(ROOT/'scripts'/'planet_geometry.py'),'exec'),globals())
control=bpy.data.objects['Planet_Control']; radius=bpy.context.scene['planet_radius']*bpy.context.scene['model_scale']; checks=[]
for factor in [1,.5,0]:
    control['flat_to_planet']=factor; control.update_tag(refresh={'OBJECT'}); bpy.context.scene.frame_set(10+round(factor*10)); bpy.context.view_layer.update(); deps=bpy.context.evaluated_depsgraph_get()
    for name in ['fallen_pole','meter','hot_roof','depot','unsure_house']:
        ob=bpy.data.objects[name]; f=ob.data.attributes['flat_position'].data[0].vector; c=ob.data.attributes['actor_center'].data[0].vector
        expected=azimuthal_rigid(Vector((f.x,f.y,f.z-radius)),(c.x,c.y),radius,factor); actual=ob.evaluated_get(deps).data.vertices[0].co
        checks.append({'factor':factor,'name':name,'error_metres':(actual-expected).length,'world':list(actual)})
maximum=max(r['error_metres'] for r in checks); result={'max_error_metres':maximum,'checks':checks,'passes_20_microns':maximum<.00002}
(ROOT/'qa'/'morph_check.json').write_text(json.dumps(result,indent=2)+'\n'); print('MORPH_CHECK',maximum,flush=True); assert maximum<.00002,result
