import bpy,json,math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
exec(compile((ROOT/'scripts'/'camera_io.py').read_text(),str(ROOT/'scripts'/'camera_io.py'),'exec'),globals())
data=json.loads((ROOT/'assets'/'camera_path.json').read_text()); scene=bpy.context.scene; camera=bpy.data.objects['Camera']; scene.render.resolution_x=1920; scene.render.resolution_y=1080
maximum=0; worst=None; count=0
for index,entry in enumerate(data['frames']):
    apply_camera(scene,camera,entry,.36); bpy.context.view_layer.update()
    for name,anchor in entry['anchors'].items():
        p=world_to_camera_view(scene,camera,convert(anchor['world'],.36)); xy=(p.x*1920,(1-p.y)*1080); error=math.hypot(xy[0]-anchor['px'][0],xy[1]-anchor['px'][1]); count+=1
        if error>maximum: maximum=error; worst={'frame':index,'anchor':name,'blender':xy,'source':anchor['px']}
result={'frames':900,'projections':count,'max_error_pixels':maximum,'worst':worst,'passes_one_pixel':maximum<1}
(ROOT/'qa'/'camera_import_check.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result),flush=True)
assert maximum<1,result
