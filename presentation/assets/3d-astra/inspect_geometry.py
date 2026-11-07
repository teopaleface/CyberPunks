"""Verify editable 3D scenes, common studio and all animated poses with Blender."""
import bpy, numpy as np, json, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
NAMES=['meter','transformer','solar','storm','helmet']
report={}; common=None
for name in NAMES:
    bpy.ops.wm.open_mainfile(filepath=str(HERE/(name+'.blend')))
    scene=bpy.context.scene; cam=scene.camera; rig=bpy.data.objects[name+' • turntable rig']
    assert scene.render.film_transparent
    assert scene.view_settings.view_transform=='Standard'
    assert scene.render.image_settings.color_mode=='RGBA'
    assert scene.frame_start==0 and scene.frame_end==29
    assert not [im for im in bpy.data.images if im.source=='FILE' and im.filepath]
    studio={'camera_location':list(cam.location),'camera_rotation':list(cam.rotation_euler),'camera_type':cam.data.type,'ortho_scale':cam.data.ortho_scale,'lights':sorted([{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'],key=lambda d:d['name'])}
    if common is None: common=studio
    else: assert studio==common, name+' studio differs'
    basis=np.array(cam.rotation_euler.to_matrix()); right,up=basis[:,0],basis[:,1]
    pose_data=[]; mesh_count=sum(o.type=='MESH' for o in scene.objects)
    total_vertices=sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH')
    for frame in range(30):
        scene.frame_set(frame); dep=bpy.context.evaluated_depsgraph_get(); mins=[]; maxs=[]
        for o in scene.objects:
            if o.type!='MESH': continue
            ev=o.evaluated_get(dep); me=ev.to_mesh(); arr=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',arr)
            mm=np.array(ev.matrix_world); q=arr.reshape(-1,3)@mm[:3,:3].T+mm[:3,3]
            xy=np.stack((q@right,q@up),axis=1); mins.append(xy.min(0)); maxs.append(xy.max(0)); ev.to_mesh_clear()
        lo=np.min(mins,axis=0); hi=np.max(maxs,axis=0)
        assert max(np.max(np.abs(lo)),np.max(np.abs(hi))) < cam.data.ortho_scale*.46,(name,frame,'clipped geometry')
        pose_data.append({'frame':frame,'rotation_degrees':[math.degrees(v) for v in rig.rotation_euler],'location':list(rig.location),'projected_bounds':[list(lo),list(hi)]})
    delta=pose_data[0]['rotation_degrees'][2]-pose_data[-1]['rotation_degrees'][2]
    assert abs(delta-120)<.001,(name,delta)
    assert all(pose_data[i]['rotation_degrees'][2]>=pose_data[i+1]['rotation_degrees'][2] for i in range(29))
    report[name]={'mesh_objects':mesh_count,'base_vertices':total_vertices,'rotation_span_degrees':delta,'poses':pose_data}
    print('SCENE_PASS',name,mesh_count,'meshes',total_vertices,'vertices',flush=True)
(HERE/'scene_verification.json').write_text(json.dumps({'status':'PASS','studio':common,'objects':report},indent=2)+'\n')
print('ALL_SCENES_PASS',flush=True)
