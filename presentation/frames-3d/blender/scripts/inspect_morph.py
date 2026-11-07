import bpy,sys
from pathlib import Path
p=Path(__file__).with_name('render_planet.py'); source=p.read_text(); source=source[:source.rindex("if args.mode=='morph':")]; exec(compile(source,str(p),'exec'),globals())
for ff in [1,.5,0]:
    configure('morph',ff)
    ob=bpy.data.objects['Planet_village']; keys=ob.data.shape_keys
    print('BEFORE',ff,[(k.name,k.value) for k in keys.key_blocks],[(fc.driver.expression,fc.driver.is_valid) for fc in keys.animation_data.drivers],flush=True)
    control.update_tag(refresh={'OBJECT'}); s.frame_set(10+round(ff*10)); bpy.context.view_layer.update()
    print('AFTER',ff,[(k.name,k.value) for k in keys.key_blocks],flush=True)
