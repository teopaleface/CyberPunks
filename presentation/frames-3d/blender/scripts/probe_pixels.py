import sys
from pathlib import Path
p=Path(__file__).with_name('render_planet.py'); sys.argv=['probe','--','--mode','preview']; exec(compile(p.read_text().rsplit("if args.mode=='morph':",1)[0],str(p),'exec'))
configure('storm'); deps=bpy.context.evaluated_depsgraph_get()
from bpy_extras.view3d_utils import region_2d_to_origin_3d
from mathutils import Vector
frame=cam.data.view_frame(scene=s); bottomleft=frame[0]
for x,y in [(1274,754),(1260,748),(1284,758),(1270,770)]:
 q=cam.data.view_frame(scene=s); local=q[3].lerp(q[0],x/1920).lerp(q[2].lerp(q[1],x/1920),1-y/1080)
 # use inverse projection convention explicitly
 sx=(x/1920*2-1); sy=(1-y/1080)*2-1; tan=math.tan(math.radians(30)/2)
 local=Vector(((sx+2*cam.data.shift_x)*tan*16/9,(sy+2*cam.data.shift_y*16/9)*tan,-1)); ray=cam.matrix_world.to_3x3()@local
 hit,pt,no,face,obj,ma=s.ray_cast(deps,cam.location,ray.normalized())
 print('HIT_WORLD',list(pt)); ev=obj.evaluated_get(deps); poly=ev.data.polygons[face]; print('FACE',poly.area,[list(ev.data.vertices[v].co) for v in poly.vertices], 'ORIGINAL', [list(obj.data.vertices[v].co) for v in obj.data.polygons[face].vertices]); print('PIXEL',x,y,hit,obj.name if obj else None,face,obj.data.materials[obj.data.polygons[face].material_index].name if obj and obj.type=='MESH' and face>=0 and face<len(obj.data.polygons) else '')
 for k in range(8):
  if not hit: break
  hit,pt,no,face,obj,ma=s.ray_cast(deps,pt+ray.normalized()*.0001,ray.normalized()); print(' BEHIND',obj.name if obj else None,obj.data.materials[obj.data.polygons[face].material_index].name if obj and obj.type=='MESH' and 0<=face<len(obj.data.polygons) else '')
