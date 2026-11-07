import bpy,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).with_name('render_planet.py'); source=p.read_text(); source=source[:source.rindex("if args.mode=='morph':")]; exec(compile(source,str(p),'exec'),globals()); configure('storm')
for px,py in [(830,690),(810,730),(1240,360)]:
    xx=(px/1920-.5)*cam.data.sensor_width/cam.data.lens; yy=(.5-py/1080)*cam.data.sensor_width/cam.data.lens/(1920/1080)
    direction=cam.matrix_world.to_quaternion()@Vector((xx,yy,-1)).normalized()
    hit,pos,norm,face,obj,matrix=s.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction)
    print('RAY',px,py,hit,obj.name if obj else None,face,obj.data.materials[obj.data.polygons[face].material_index].name if obj and face>=0 else '')
for obj in bpy.data.objects:
    if obj.particle_systems: print('PARTICLES',obj.name,[(ps.settings.name,len(ps.particles)) for ps in obj.particle_systems])
