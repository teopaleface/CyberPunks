"""Keep the fallen-pole assembly visible independently of the cotton cloud and rain."""
import bpy,bmesh,sys
from pathlib import Path

def ensure_damage():
    if bpy.data.collections.get('damage'): return
    src=bpy.data.objects['Planet_storm']; coll=bpy.data.collections.new('damage'); bpy.context.scene.collection.children.link(coll)
    ob=src.copy(); ob.data=src.data.copy(); ob.name='Planet_damage'; coll.objects.link(ob)
    names={'Weathered grey concrete','Graphite power wire'}
    def keep(obj,damage):
        bm=bmesh.new(); bm.from_mesh(obj.data)
        remove=[f for f in bm.faces if (obj.data.materials[f.material_index].name in names)!=damage]
        bmesh.ops.delete(bm,geom=remove,context='FACES'); bm.to_mesh(obj.data); bm.free(); obj.data.update()
        assert obj.data.attributes.get('flat_position') and obj.data.attributes.get('actor_center')
    keep(ob,True); keep(src,False)
    ob.hide_render=False; ob.hide_viewport=False
    print('DAMAGE_SPLIT',len(ob.data.polygons),len(ob.animation_data.drivers) if ob.animation_data else 0,flush=True)
ensure_damage()
if '--save' in sys.argv: bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
