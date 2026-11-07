"""Exact Three.js Y-up camera to Blender Z-up, including the supplied off-axis frustum."""
import math
from mathutils import Vector,Matrix

def convert(p,radius): return Vector((p[0]*radius,-p[2]*radius,p[1]*radius))
def look_at(camera,position,target):
    camera.location=position; forward=(Vector(target)-camera.location).normalized(); up=Vector((0,0,1)); right=forward.cross(up)
    if right.length<1e-8: right=Vector((1,0,0))
    right.normalize(); actual_up=right.cross(forward).normalized()
    camera.rotation_euler=Matrix(((right.x,actual_up.x,-forward.x),(right.y,actual_up.y,-forward.y),(right.z,actual_up.z,-forward.z))).to_quaternion().to_euler()
def apply_camera(scene,camera,entry,radius,focus=None):
    data=entry['camera']; look_at(camera,convert(data['position'],radius),convert(data['target'],radius))
    camera.data.type='PERSP'; camera.data.sensor_fit='HORIZONTAL'; camera.data.lens=85
    camera.data.sensor_width=2*85*math.tan(math.radians(data['fov'])/2)*(16/9)
    camera.data.shift_x=data['shift'][0]/2; camera.data.shift_y=data['shift'][1]*.5*(9/16)
    camera.data.clip_start=.001; camera.data.clip_end=1000
    aperture=float(data.get('aperture',0))*radius; camera.data.dof.use_dof=aperture>0
    if aperture>0: camera.data.dof.aperture_fstop=max(1,.085/(2*aperture))
    if focus:
        focus.location=(0,0,radius+.015); camera.data.dof.focus_object=focus
    camera.data.dof.aperture_blades=9; scene.camera=camera
