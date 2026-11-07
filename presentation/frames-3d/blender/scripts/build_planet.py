"""Build Planet Daybreak from the original deterministic village. All downloads are local CC0 assets."""
from pathlib import Path
import bpy,bmesh,math,random,json,sys,time
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'scripts'/'build_scene.py'
source=base.read_text(); source=source[:source.index('bpy.ops.wm.save_as_mainfile')]
random.seed(270611)
# A small, organic hero village on the front cap. Other original houses continue on the far side.
hero=[(-6.4,-.6),(-5.1,-3.4),(-2.9,-5.4),(-.7,-6.3),(4.7,3.3),(6.3,.4),(5.,-4.8),(-1.1,6.2),(2.6,5.8),(-8.3,1.2),(-8.6,-1.5),(-7.7,-4.2),(-6.2,-6.5),(-3.8,-7.9),(-1.1,-8.2),(1.8,-7.2),(4.,-6.8),(6.6,-5.7),(7.8,-3.3),(8.5,-.6),(7.4,2.5),(6.2,5.3),(3.9,7.2),(1.3,8.),(-1.6,8.5),(-4.3,7.5),(-7.1,5.8)]
back=[((18+random.uniform(-1.2,1.2))*math.cos(i*math.tau/13),(18+random.uniform(-1.2,1.2))*math.sin(i*math.tau/13)) for i in range(13)]
for i,p0 in {9:(-3.7,5.2),11:(-4.9,-1.9),14:(-.8,-3.3),17:(3.5,-3.8),20:(3.5,.1),22:(2.3,4.5),24:(-2.,6.2)}.items(): hero[i]=p0
planet_layout=hero+back
source=source.replace("roof('House',x,y,z+h,w,d,.6)","roof('House',x,y,z+h,w,d,random.uniform(.44,.86))")
source=source.replace("(x,y,1.99),(x,y,3.05),.026", "(x,y,1.7),(x,y,2.32),.014")
source=source.replace("(x,y,3.12),(.18,.18,.18)","(x,y,2.38),(.085,.085,.085)")
start=source.index('houses=[]'); end=source.index('# Field board',start)
source=source[:start]+'''house_specs=[]
original_house=house
def house(x,y,w=1.55,d=1.75,h=1.05,annex=False,z=.29):
    before=set(active.objects); original_house(x,y,w,d,h,annex,z)
    for part in set(active.objects)-before: part['planet_center']=[x,y*.72]
    house_specs.append((x,y*.72,w,d*.72,h,z))
houses=[]
for i,(xx,yy) in enumerate(planet_layout):
    x=xx+random.uniform(-.18,.18); y=yy/.72+random.uniform(-.18,.18)
    house(x,y,random.uniform(1.10,1.74),random.uniform(1.4,2.13),random.uniform(.72,1.35),annex=i%6==0)
    houses.append((x,y))
    if i%3==0: tree(x+1.0,y+.8,random.uniform(.65,.9))
'''+source[end:]
start=source.index('pin_specs=['); end=source.index('pins=[]',start)
source=source[:start]+'''pin_specs=[(0,-.7,-6.3/.72,.4),(0,5,-4.8/.72,.7),(0,-1.1,6.2/.72,.95),(1,6.3,.4/.72,.4),(1,4.7,3.3/.72,.7),(1,2.6,5.8/.72,.95),(2,-6.4,-.6/.72,.4),(2,-5.1,-3.4/.72,.7),(2,-2.9,-5.4/.72,.95)]
'''+source[end:]
exec(compile(source,str(base),'exec'),globals())
random.seed(270611)
S=.04; R=9.; LAT=0.
ASSETS=json.loads((ROOT/'assets'/'manifest.json').read_text())
A={a['name']:a for a in ASSETS}
# Delete only staging that belongs to the old white photographs.
for cname in ['stage','problems','light_storm','light_where','light_problems','light_map','light_dawn','cameras']:
    for o in list(COL[cname].objects): bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(COL[cname]); del COL[cname]
for n in ['terrain','foliage','details','lights','map_graphic','anchors','studio','hero_camera']:
    collection(n)
for o in list(COL['village'].objects):
    if o.name.startswith(('Thin white base','Land between','Parallel field','Sunflower field edge')): bpy.data.objects.remove(o,do_unlink=True)
for o in list(COL['depot'].objects):
    if o.name.startswith(('Depot cutaway','Depot shed','Recessed garage','White garage','Garage jamb')): bpy.data.objects.remove(o,do_unlink=True)

for o in list(COL['village'].objects):
    if o.name.startswith(('Concrete distribution','White crossarm','Porcelain insulator','Suspended dark')): bpy.data.objects.remove(o,do_unlink=True)
for o in list(COL['routes'].objects):
    if o.name.startswith('House tether'): bpy.data.objects.remove(o,do_unlink=True)
exec(compile((ROOT/'scripts'/'planet_geometry.py').read_text(),str(ROOT/'scripts'/'planet_geometry.py'),'exec'),globals())

def color(h): return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))
def paint(name,h,rough=.85): return mat(name,h,rough)
def pbr(name,aid,scale=1.,tint=None,tint_mix=0.,bump_strength=.35):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; p=nt.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value=.85; p.inputs['Specular IOR Level'].default_value=.18
    uv=nt.nodes.new('ShaderNodeTexCoord'); mapping=nt.nodes.new('ShaderNodeVectorMath'); mapping.operation='SCALE'; mapping.inputs[3].default_value=scale; nt.links.new(uv.outputs['UV'],mapping.inputs[0])
    texs={}
    for k in ['Diffuse','Rough','nor_gl','Displacement']:
        f=A[aid]['files'].get(k)
        if not f: continue
        t=nt.nodes.new('ShaderNodeTexImage'); t.label=aid+' '+k; t.image=bpy.data.images.load(str(ROOT/'assets'/f['local']),check_existing=True)
        if k!='Diffuse': t.image.colorspace_settings.name='Non-Color'
        t.extension='REPEAT'; nt.links.new(mapping.outputs['Vector'],t.inputs['Vector']); texs[k]=t
    if tint:
        mix=nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MIX'; mix.inputs[0].default_value=tint_mix; mix.inputs[2].default_value=(*color(tint),1)
        nt.links.new(texs['Diffuse'].outputs['Color'],mix.inputs[1]); nt.links.new(mix.outputs[0],p.inputs['Base Color'])
    else: nt.links.new(texs['Diffuse'].outputs['Color'],p.inputs['Base Color'])
    if 'Rough' in texs:
        remap=nt.nodes.new('ShaderNodeMapRange'); remap.inputs['To Min'].default_value=.55; remap.inputs['To Max'].default_value=.98
        nt.links.new(texs['Rough'].outputs['Color'],remap.inputs['Value']); nt.links.new(remap.outputs[0],p.inputs['Roughness'])
    if 'nor_gl' in texs:
        normal=nt.nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value=bump_strength
        nt.links.new(texs['nor_gl'].outputs['Color'],normal.inputs['Color']); nt.links.new(normal.outputs['Normal'],p.inputs['Normal'])
    if 'Displacement' in texs:
        bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.18; bump.inputs['Distance'].default_value=.00035
        nt.links.new(texs['Displacement'].outputs['Color'],bump.inputs['Height'])
        if 'normal' in locals(): nt.links.new(normal.outputs['Normal'],bump.inputs['Normal'])
        nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
PLASTER=pbr('PH limewash | worn ivory','white_plaster_rough_01',1.3,'EEE8DD',.20,.85)
ROOF=pbr('PH terracotta roof tiles','clay_roof_tiles_02',1.4,'B5523A',.12,.85)
GRAVEL=pbr('PH utility yard gravel','gravel_road',1.4,None,0,.55)
ASPHALT=pbr('PH worn asphalt','asphalt_02',.65,None,0,.4)
BARK=pbr('PH walnut tree bark','bark_brown_02',1,None,0,.6)
WOOD=pbr('PH walnut timber','european_walnut_veneer_04',1,None,0,.4)
GRASS=pbr('PH grass and moss ground','grass_ground',.6,'4E6B35',.55,.55)
IVORY=paint('Matte miniature ivory','EEE8DD',.78); CONCRETE=paint('Weathered grey concrete','9F9C8C',.92)
FRAME=paint('Old green-brown joinery','3A4331',.9); RUBBER=paint('Soft tyre rubber','242925',.95); NAVY=paint('PPC navy map ground','000F1E',.94)
PPC=paint('PPC orange | FA4616','FA4616',.75); CYAN=paint('PPC cyan | 00A3E0','00A3E0',.64); ELECTRIC=paint('PPC blue | 163FE8','163FE8',.64)
SKIN=paint('Painted worker skin','BB8F69',.9); NAVY_CLOTH=paint('Navy work trousers','283E47',.95); YELLOW=paint('Sunflower petals','E8B32A',.88); SEED=paint('Sunflower seeds','4F351F',1)
LEAF=paint('Translucent walnut foliage','4E6B35',.9)
nt=LEAF.node_tree; p=nt.nodes.get('Principled BSDF'); trans=nt.nodes.new('ShaderNodeBsdfTranslucent'); trans.inputs[0].default_value=(*color('6C8A45'),1)
info=nt.nodes.new('ShaderNodeObjectInfo'); noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=170
ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(*color('293C19'),1); ramp.color_ramp.elements[1].color=(*color('8C9A42'),1)
nt.links.new(noise.outputs['Fac'],ramp.inputs[0]); nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
mix=nt.nodes.new('ShaderNodeMixShader'); mix.inputs[0].default_value=.28; nt.links.new(p.outputs[0],mix.inputs[1]); nt.links.new(trans.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
HAIR=paint('Fine flock fibres','596C32',.98); STONE=paint('Dark irregular fieldstone','4A4C3D',1)
WINDOW=paint('Warm miniature window','DAB16B',.42); wp=WINDOW.node_tree.nodes.get('Principled BSDF'); wp.inputs['Emission Color'].default_value=(*color('FFC46E'),1); wp.inputs['Emission Strength'].default_value=.8
HEAD=paint('Warm truck headlights','FFE0A0',.38); hp=HEAD.node_tree.nodes.get('Principled BSDF'); hp.inputs['Emission Color'].default_value=(*color('FFD18B'),1); hp.inputs['Emission Strength'].default_value=4
CAB=paint('Smoked cab glazing','26343A',.32)
for m in [PPC,CYAN,ELECTRIC]:
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Sheen Weight'].default_value=.35; p.inputs['Sheen Roughness'].default_value=.5
    nt=m.node_tree; weave=nt.nodes.new('ShaderNodeTexNoise'); weave.inputs['Scale'].default_value=400; weave.inputs['Detail'].default_value=1
    bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value=.00008; bump.inputs['Strength'].default_value=.15; nt.links.new(weave.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])

window_mats={}; plaster_variants={}
# Soil-darkened limewash at the foot of each building, retaining scanned plaster normals.
p=PLASTER.node_tree.nodes.get('Principled BSDF'); nt=PLASTER.node_tree; old=next(link.from_socket for link in nt.links if link.to_socket==p.inputs['Base Color'])
height=nt.nodes.new('ShaderNodeAttribute'); height.attribute_name='model_height'; ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.006; ramp.color_ramp.elements[0].color=(*color('766A50'),1); ramp.color_ramp.elements[1].position=.023; ramp.color_ramp.elements[1].color=(1,1,1,1)
nt.links.new(height.outputs['Fac'],ramp.inputs[0]); grime=nt.nodes.new('ShaderNodeMixRGB'); grime.blend_type='MULTIPLY'; grime.inputs[0].default_value=1; nt.links.new(old,grime.inputs[1]); nt.links.new(ramp.outputs[0],grime.inputs[2]); nt.links.new(grime.outputs[0],p.inputs['Base Color'])
# Pigment rubs, limewash erosion and damp speckles remain visible in the macro views.
noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=24; noise.inputs['Detail'].default_value=5; noise.inputs['Roughness'].default_value=.78
tc=nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['UV'],noise.inputs['Vector'])
stain=nt.nodes.new('ShaderNodeValToRGB'); stain.color_ramp.elements[0].position=.33; stain.color_ramp.elements[0].color=(*color('6F705C'),1); stain.color_ramp.elements[1].position=.58; stain.color_ramp.elements[1].color=(1,1,1,1)
nt.links.new(noise.outputs['Fac'],stain.inputs[0]); weather=nt.nodes.new('ShaderNodeMixRGB'); weather.blend_type='MULTIPLY'; weather.inputs[0].default_value=.62; nt.links.new(grime.outputs[0],weather.inputs[1]); nt.links.new(stain.outputs[0],weather.inputs[2]); nt.links.new(weather.outputs[0],p.inputs['Base Color'])
# The lower hemisphere shows real earthy material, interrupted by moss, not painted green.
p=GRASS.node_tree.nodes.get('Principled BSDF'); nt=GRASS.node_tree; old=next(link.from_socket for link in nt.links if link.to_socket==p.inputs['Base Color'])
earth=nt.nodes.new('ShaderNodeTexImage'); earth.image=bpy.data.images.load(str(ROOT/'assets'/A['gravel_road']['files']['Diffuse']['local']),check_existing=True); earth.extension='REPEAT'
dark=nt.nodes.new('ShaderNodeMixRGB'); dark.blend_type='MULTIPLY'; dark.inputs[0].default_value=1; dark.inputs[2].default_value=(*color('5C4935'),1); nt.links.new(earth.outputs['Color'],dark.inputs[1])
mask=nt.nodes.new('ShaderNodeAttribute'); mask.attribute_name='earth_crust'; mixsoil=nt.nodes.new('ShaderNodeMixRGB'); nt.links.new(old,mixsoil.inputs[1]); nt.links.new(dark.outputs[0],mixsoil.inputs[2]); nt.links.new(mixsoil.outputs[0],p.inputs['Base Color'])
rest=nt.nodes.new('ShaderNodeAttribute'); rest.attribute_name='flat_position'; patches=nt.nodes.new('ShaderNodeTexNoise'); patches.inputs['Scale'].default_value=29; patches.inputs['Detail'].default_value=4; nt.links.new(rest.outputs['Vector'],patches.inputs['Vector'])
patch_ramp=nt.nodes.new('ShaderNodeValToRGB'); patch_ramp.color_ramp.elements[0].position=.40; patch_ramp.color_ramp.elements[0].color=(0,0,0,1); patch_ramp.color_ramp.elements[1].position=.64; patch_ramp.color_ramp.elements[1].color=(.9,.9,.9,1); nt.links.new(patches.outputs['Fac'],patch_ramp.inputs[0])
maximum=nt.nodes.new('ShaderNodeMath'); maximum.operation='MAXIMUM'; nt.links.new(mask.outputs['Fac'],maximum.inputs[0]); nt.links.new(patch_ramp.outputs[0],maximum.inputs[1]); nt.links.new(maximum.outputs[0],mixsoil.inputs[0])
nt=CONCRETE.node_tree; cp=nt.nodes.get('Principled BSDF'); cn=nt.nodes.new('ShaderNodeTexNoise'); cn.inputs['Scale'].default_value=85
cb=nt.nodes.new('ShaderNodeBump'); cb.inputs['Distance'].default_value=.00015; cb.inputs['Strength'].default_value=.45; nt.links.new(cn.outputs['Fac'],cb.inputs['Height']); nt.links.new(cb.outputs['Normal'],cp.inputs['Normal'])
# Real particle hair varies by strand, like several colours of fine model flock.
nt=HAIR.node_tree; hp=nt.nodes.get('Principled BSDF'); hi=nt.nodes.new('ShaderNodeHairInfo'); cr=nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color=(*color('263B1C'),1); cr.color_ramp.elements[1].color=(*color('8B994B'),1); nt.links.new(hi.outputs['Random'],cr.inputs[0]); nt.links.new(cr.outputs[0],hp.inputs['Base Color'])
# Repaint the original individual components, retaining every house and road layout.
for cname in ['village','depot','storm','parked','dispatch','routes']:
    for o in list(COL[cname].objects):
        if o.type not in ['MESH','CURVE']: continue
        n=o.name.lower(); old=o.data.materials[0] if o.data.materials else WHITE
        if 'faceted white walnut' in n: continue
        if 'tyre' in n: m=RUBBER
        elif 'glazing' in n: m=CAB
        elif 'headlamp' in n: m=HEAD
        elif 'concrete' in n or 'pole stump' in n or 'crossarm' in n: m=CONCRETE
        elif 'insulator' in n: m=IVORY
        elif 'wire' in n: m=WIRE
        elif 'trunk' in n: m=BARK
        elif 'fence' in n or 'post' in n: m=WOOD
        elif 'depot raised yard' in n or 'parking bay' in n: m=GRAVEL
        elif 'card roof' in n: m=ROOF
        elif 'recess back' in n:
            m=WINDOW if o.dimensions.z<.55 else FRAME
        elif any(x in n for x in ['mullion','crossbar','side jamb','side lintel']): m=FRAME
        elif 'side inset' in n: m=WINDOW
        elif 'ridge' in n: m=ROOF
        elif 'cloud' in n or 'rain' in n or 'filament' in n: continue
        elif old==ORANGE: m=IVORY if cname in ['parked','dispatch','routes'] or 'truck' in n else PPC
        elif old==BLUE: m=CYAN
        elif old==GREEN: m=ELECTRIC
        elif o.parent and ('truck' in o.parent.name.lower() or 'convoy' in o.parent.name.lower()): m=IVORY if old in [WHITE,EDGE] else old
        else: m=PLASTER
        if m==WINDOW:
            center=o.matrix_world.translation; i=min(range(len(houses)),key=lambda k:(houses[k][0]-center.x)**2+(houses[k][1]*.72-center.y)**2)
            if i not in window_mats:
                wm=WINDOW.copy(); wm.name='Window house %02d'%i; scene['window_house_%02d'%i]=1.
                dr=wm.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].driver_add('default_value').driver; dr.expression='strength'; v=dr.variables.new(); v.name='strength'; v.targets[0].id_type='SCENE'; v.targets[0].id=scene; v.targets[0].data_path='["window_house_%02d"]'%i; window_mats[i]=wm
            m=window_mats[i]
        if m==PLASTER and 'planet_center' in o:
            hx,hy=o['planet_center']; key=round(hx,4),round(hy,4)
            if key not in plaster_variants:
                variant=PLASTER.copy(); variant.name='Hand-mixed limewash %02d'%len(plaster_variants); nt=variant.node_tree; bs=nt.nodes.get('Principled BSDF'); previous=next(link.from_socket for link in nt.links if link.to_socket==bs.inputs['Base Color'])
                tint=nt.nodes.new('ShaderNodeMixRGB'); tint.blend_type='MULTIPLY'; tint.inputs[0].default_value=.38; tint.inputs[2].default_value=(*color(random.choice(['D4C7AB','DED8CB','C8C9B4','E3DDCF','C7BEAA','E7DFC7'])),1); nt.links.new(previous,tint.inputs[1]); nt.links.new(tint.outputs[0],bs.inputs['Base Color']); plaster_variants[key]=variant
            m=plaster_variants[key]
        o.data.materials.clear(); o.data.materials.append(m)
# White die-cast utility fleet with an orange stripe and fine panel seams.
for cname in ['parked','dispatch','routes','storm']:
    active=COL[cname]
    for parent in [ob for ob in list(COL[cname].objects) if ob.type=='EMPTY' and any(k in ob.name.lower() for k in ['truck','convoy'])]:
        for child in parent.children:
            if child.type=='MESH' and child.data.materials and child.data.materials[0]==PPC: child.data.materials.clear(); child.data.materials.append(IVORY)
        for side in [-1,1]:
            stripe=box('Thin PPC orange fleet stripe',(-.08,side*.355,.57),(1.34,.018,.075),PPC,.005); stripe.parent=parent
# Satin ribbons: flatten each round cross-section into a broad thin tape before wrapping.
for o in COL['routes'].objects:
    if o.type=='CURVE' and o.name.startswith('Route '):
        # Curve bevel profile is evaluated to mesh below and flattened in its own up direction.
        o['ribbon']=True
# Small sheds and vegetable beds make the dense village read as hand-built plots.
active=COL['village']
for i,(hx,hy0) in enumerate(houses[:27]):
    if i%3: continue
    hy=hy0*.72; x,y=hx+.95,hy+.72
    shed=box('Small weathered garden shed',(x,y,.48),(.58,.65,.50),FRAME,.012); shed['planet_center']=[hx,hy]
    before=set(active.objects); roof('Small shed',x,y,.73,.62,.7,.24,PLASTER)
    for ob in set(active.objects)-before:
        ob['planet_center']=[hx,hy]
        if 'roof' in ob.name or 'ridge' in ob.name: ob.data.materials.clear(); ob.data.materials.append(ROOF)
    for j in range(12):
        veg=sphere('Garden cabbage',(hx-1.05+(j%3)*.13,hy+.7+(j//3)*.13,.23),(.065,.065,.05),LEAF,True); veg['planet_center']=[hx,hy]
# Individual shingles provide imperfect edges and overlap, beyond the scanned PBR normal map.
bpy.context.view_layer.update()
active=COL['village']; tiles_v=[]; tiles_f=[]; tiles_uv=[]; tile_attach=[]
for o in list(COL['village'].objects):
    if 'card roof' not in o.name.lower(): continue
    w,d,h=[max(v.co[a] for v in o.data.vertices)-min(v.co[a] for v in o.data.vertices) for a in range(3)]; nx=max(4,round(w/.15)); ny=max(6,round(d/.16)); mw=o.matrix_world.copy()
    for ix in range(nx):
        for iy in range(ny):
            x=-w/2+(ix+.55)*w/nx+random.uniform(-.008,.008); y=-d/2+(iy+.5)*d/ny+random.uniform(-.008,.008)
            sx=w/nx*1.08; sy=d/ny*.98; idx=len(tiles_v)
            for u in [0,1]:
                for j in range(5):
                    v=j/4; co=mw@Vector((x+(u-.5)*sx,y+(v-.5)*sy,h/2+.013*math.sin(math.pi*v)+.007))
                    tiles_v.append(tuple(co)); tiles_uv.append((co.x*.65,co.y*.65)); tile_attach.append(tuple(o['planet_center']) if 'planet_center' in o else None)
            for j in range(4): tiles_f.append((idx+j,idx+j+1,idx+6+j,idx+5+j))
mesh('Hand-laid irregular barrel roof tiles',tiles_v,tiles_f,ROOF)
# Large old walnut trees form the visual hierarchy of a real village model.
active=COL['village']
for x,y,sc in [(-1.8,2.7,1.25),(.2,3.8,1.2),(1.8,1.7,1.13),(-3.4,-.1,.9),(5.8,5.1,.9)]: tree(x,y,sc)
bpy.context.view_layer.update()
trunk_centers=[(o.matrix_world.translation.x,o.matrix_world.translation.y) for o in COL['village'].objects if o.name.startswith('Walnut trunk')]
active=COL['village']
for tx,ty in trunk_centers:
    for dx,dy,zz in [(-.35,.1,1.5),(.32,.25,1.6),(.14,-.3,1.4),(-.15,-.25,1.7)]:
        branch=rod('Walnut branch structure',(tx,ty,.85),(tx+dx,ty+dy,zz),.028,BARK,10); branch['planet_center']=[tx,ty]

# Real leaf cards replace the faceted crown balls. A single mesh keeps the scene practical.
bpy.context.view_layer.update()
active=COL['foliage']; lv=[]; lf=[]; leaf_attach=[]
for o in list(COL['village'].objects)+list(COL['depot'].objects):
    if not o.name.startswith('Faceted white walnut'): continue
    center=o.matrix_world.translation; scales=Vector(o.scale)*1.22
    attachment=min(trunk_centers,key=lambda p:(p[0]-center.x)**2+(p[1]-center.y)**2)
    for j in range(350):
        az=random.uniform(0,math.tau); zz=random.uniform(-1,1); rr=random.uniform(.48,1.03); ss=math.sqrt(1-zz*zz)
        pos=center+Vector((ss*math.cos(az)*scales.x,ss*math.sin(az)*scales.y,zz*scales.z))*rr
        a=random.uniform(0,math.tau); le=random.uniform(.055,.115); wi=le*.4
        u=Vector((math.cos(a)*le,math.sin(a)*le,random.uniform(-.04,.04))); v=Vector((-math.sin(a)*wi,math.cos(a)*wi,.008))
        leaf_attach.extend([attachment]*5)
        idx=len(lv); lv.extend([tuple(pos-u),tuple(pos+v),tuple(pos+u),tuple(pos-v),tuple(pos+Vector((0,0,.018)))])
        lf.extend([(idx,idx+1,idx+4),(idx+1,idx+2,idx+4),(idx+2,idx+3,idx+4),(idx+3,idx,idx+4)])
    bpy.data.objects.remove(o,do_unlink=True)
mesh('Translucent individual walnut leaf clusters',lv,lf,LEAF)
# The physical road network lies on the soil, rather than on a white rectangular board.
active=COL['village']
def road_strip(name,axis,center,length,width,material):
    vs=[]; fs=[]; count=math.ceil(length/.19)
    for i in range(count+1):
        along=-length/2+length*i/count
        for j in range(5):
            across=-width/2+width*j/4
            vs.append((along,center+across,.235) if axis=='X' else (center+across,along,.238))
    for i in range(count):
        for j in range(4): a=i*5+j; fs.append((a,a+1,a+6,a+5))
    ob=mesh(name,vs,fs,material)
    for poly in ob.data.polygons: poly.use_smooth=True
for o in list(COL['depot'].objects):
    if o.name.startswith('Depot raised yard'): bpy.data.objects.remove(o,do_unlink=True)
active=COL['depot']; road_strip('Depot gravel yard','X',-3.0,9.4,5.0,GRAVEL)
for v in bpy.data.objects['Depot gravel yard'].data.vertices: v.co.x-=15
new_paths=[
 [(-2.1,2.35,.26),(-.7,2.2,.26),(.2,1,.26),(.65,-.8,.26),(1.7,-3.1,.26),(1.9,-5.5,.26),(.1,-6.4,.26)],
 [(-2.1,2.65,.26),(-.6,2.65,.26),(1.6,2.8,.26),(3.2,2.6,.26),(4.4,1.5,.26),(5.3,.0,.26),(5.1,-1.1,.26)],
 [(-2.1,2.05,.26),(-1.2,.5,.26),(-2.1,-.3,.26),(-3.8,-1.5,.26),(-4.1,-3.5,.26),(-3,-4.9,.26)]]
new_paths=[rounded(path,.6) for path in new_paths]
def strip_path(name,points,width,material):
    dense=[Vector(points[0])]
    for aa,bb in zip(points,points[1:]):
        aa,bb=Vector(aa),Vector(bb); count=max(1,math.ceil((bb-aa).length/.11)); dense.extend(aa.lerp(bb,j/count) for j in range(1,count+1))
    vs=[]; fs=[]
    for i,pt in enumerate(dense):
        d=dense[min(i+1,len(dense)-1)]-dense[max(0,i-1)]; side=Vector((-d.y,d.x,0)).normalized()*width/2
        for j in range(5):
            edge=1+.075*math.sin(i*.73)+.045*math.sin(i*2.17)
            pp=pt+side*(-1+j*.5)*(edge if j in [0,4] else 1); pp.z-=.018 if j in [1,3] else .026 if j in [0,4] else 0; vs.append(tuple(pp))
    for i in range(len(dense)-1):
        for j in range(4): a=i*5+j; fs.append((a,a+1,a+6,a+5))
    ob=mesh(name,vs,fs,material)
    for p in ob.data.polygons: p.use_smooth=True
    return ob
active=COL['village']
for i,points in enumerate(new_paths): strip_path('Winding rural dirt and gravel road',[(x,y,.145) for x,y,z in points],1.18 if i==0 else 1.0,GRAVEL)
for x,y in [(-6.8,1.4),(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8),(1,-5.7)]:
    before=set(active.objects); pole(x,y)
    for ob in set(active.objects)-before:
        if ob.type=='MESH':
            ob.data.materials.clear(); ob.data.materials.append(IVORY if 'insulator' in ob.name else CONCRETE); ob['planet_center']=[x,y]
def catenary_points(x1,y1,x2,y2,z=2.87,sag=.25):
    length=math.hypot(x2-x1,y2-y1); lo,hi=length*.03,length*100
    for _ in range(50):
        a=(lo+hi)/2; drop=a*(math.cosh(length/(2*a))-1)
        if drop>sag: lo=a
        else: hi=a
    a=(lo+hi)/2; edge=a*math.cosh(length/(2*a)); out=[]
    for j in range(49):
        t=j/48; zz=z+a*math.cosh((t-.5)*length/a)-edge; out.append((x1+(x2-x1)*t,y1+(y2-y1)*t,zz))
    return out
for (x1,y1),(x2,y2) in zip([(-6.8,1.4),(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8)],[(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8),(1,-5.7)]):
    for off in [-.32,0,.32]:
        wire=curve('Fine catenary distribution wire',catenary_points(x1+off,y1,x2+off,y2),.007,WIRE); wire['wire_line']=[x1,y1,x2,y2,off]
for yy in [-7.04,-3.04,.8]:
    for sign in [-1,1]:
        points=[(sign*(13+j*.25),yy+.18*math.sin(j*.28),.21) for j in range(49)]
        strip_path('Far-side rural dirt lane',points,.9,GRAVEL)
# Short worn asphalt service pads in the utility yard, while village roads remain dirt.
active=COL['depot']
for xx in [-18.2,-16.7,-15.2]:
    road_strip('Depot asphalt service pad','Y',xx,2.3,.60,ASPHALT)
    pad=[o for o in active.objects if o.name.startswith('Depot asphalt service pad')][-1]
    for vertex in pad.data.vertices: vertex.co.y-=4.4; vertex.co.z=.25
active=COL['village']
# The depot is now an open, working workshop with deep bays and real warm practicals.
active=COL['depot']
box('Depot plaster back wall',(-17,-.68,1.1),(4.7,.1,1.6),PLASTER,.015)
for xx in [-19.35,-14.65]: box('Depot end wall',(xx,-1.32,1.1),(.1,1.35,1.6),PLASTER,.015)
for xx in [-19.35,-17.8,-16.25,-14.65]: box('Depot bay column',(xx,-1.97,1.1),(.13,.13,1.6),PLASTER,.014)
for xx in [-18.5,-17,-15.5]:
    for z in [.62,.98]: box('Walnut workshop shelf',(xx,-.91,z),(1.12,.33,.07),WOOD,.008)
    for j in range(3): box('Stored repair kit',(xx-.35+j*.3,-.91,.75),(.21,.2,.2),PPC if j%2 else FRAME,.018)
roof('Depot weathered tiled shelter',-17,-1.32,1.95,4.9,1.5,.52,PLASTER)
for o in COL['depot'].objects:
    if o.name.startswith('Depot weathered') and ('roof' in o.name or 'ridge' in o.name): o.data.materials.clear(); o.data.materials.append(ROOF)
# Solar panels and tampered meter belong to real houses, rather than separate vignettes.
active=COL['details']
box('Tampered meter enclosure',(-6.4,-1.24,.82),(.3,.16,.38),CONCRETE,.018)
rod('Meter glass dial',(-6.4,-1.325,.85),(-6.4,-1.345,.85),.09,CAB,24)
curve('Tampering horseshoe',[( -6.10+.13*math.cos(j*math.pi/24),-1.37,.72-.13*math.sin(j*math.pi/24)) for j in range(25)],.045,PPC)
before=set(active.objects); panel=group_new('Actual hot-roof panel assembly')
box('Panel frame',(0,0,0),(.66,1.03,.035),IVORY,.008)
for ix in range(3):
    for iy in range(5): box('PV panel cell',(-.22+ix*.22,-.4+iy*.2,.024),(.204,.184,.012),SOLAR,.002)
parent_new(panel,before); panel.location=(-5.44,-3.4,1.78); panel.rotation_euler.y=-.64
# Painted figures, reflective bands and tools, anatomically proportioned to the trucks.
def worker(name,x,y,z=.25,pose='idle'):
    before=set(active.objects); p=group_new(name)
    for side in [-1,1]:
        hip=(side*.035,0,.235); knee=(side*.04,.012,.13); ankle=(side*.043,-.005,.036)
        rod('Trouser upper leg',hip,knee,.027,NAVY_CLOTH,10); rod('Trouser lower leg',knee,ankle,.023,NAVY_CLOTH,10)
        box('Work boot',(side*.044,-.018,.025),(.055,.085,.04),RUBBER,.009)
        rod('Reflective leg band',(side*.04,.005,.095),(side*.04,.005,.112),.024,IVORY,10)
    box('Hi-vis jacket',(0,0,.31),(.13,.08,.16),PPC,.027)
    box('Reflective jacket belt',(0,-.044,.29),(.132,.009,.017),IVORY,.002)
    for xx in [-.04,.04]: box('Reflective shoulder tape',(xx,-.045,.347),(.014,.009,.077),IVORY,.002)
    rod('Neck',(0,0,.388),(0,0,.405),.022,SKIN,12); sphere('Painted head',(0,-.002,.427),(.035,.032,.041),SKIN)
    sphere('White hard hat',(0,0,.461),(.047,.042,.024),IVORY)
    rod('Hard hat brim',(0,0,.449),(0,0,.458),.052,IVORY,20)
    for side in [-1,1]:
        shoulder=(side*.075,0,.367); elbow=(side*.105,-.012,.29); hand=(side*.11,-.04,.255)
        if pose in ['tools','clipboard']:
            elbow=(side*.105,-.06,.32); hand=(side*.065,-.13,.32)
        if pose=='point' and side==1: elbow=(.1,-.03,.42); hand=(.1,-.09,.48)
        rod('Jacket sleeve',shoulder,elbow,.024,PPC,10); rod('Jacket forearm',elbow,hand,.02,PPC,10); sphere('Painted gloved hand',hand,(.021,.019,.021),SKIN)
    if pose=='clipboard': box('Blank clipboard',(0,-.15,.33),(.14,.018,.12),WOOD,.006,(-.3,0,0))
    if pose=='tools': box('Repair tool case',(0,-.15,.28),(.15,.08,.08),PPC,.008)
    parent_new(p,before); p.location=(x,y,z); return p
for i,(x,y) in enumerate([(-18,-4.8),(-16.3,-4.6),(-14.8,-4.45),(-12.8,-3.8)]): worker('Depot crew %d'%i,x,y,.34,['tools','clipboard','idle','tools'][i])
worker('Night crew at snapped pole',1.55,-.5,.25,'point'); worker('Second night crew',2.6,-1.6,.25,'tools')
worker('Roof inspection crew',-4.4,-4.2,.25,'clipboard')
# Coffee thermos, a dog, and laundry are deliberate scale cues.
rod('Coffee thermos',(-15.0,-4.35,.87),(-15,-4.35,.98),.027,WOOD,16)
sphere('Dog body',(-16.8,-4.8,.47),(.16,.06,.075),WOOD)
sphere('Dog head',(-16.62,-4.8,.54),(.06,.05,.06),WOOD)
for xx in [-16.9,-16.7]:
    for yy in [-4.84,-4.76]: rod('Dog leg',(xx,yy,.44),(xx,yy,.34),.016,WOOD,8)
curve('Dog tail',[(-16.95,-4.8,.48),(-17.02,-4.8,.58),(-17.08,-4.8,.6)],.016,WOOD,True)
for xx in [-4.8,-2.0]: rod('Laundry post',(xx,3.8,.25),(xx,3.8,1.0),.025,WOOD)
curve('Laundry line',[(-4.8,3.8,1),(-3.4,3.8,.93),(-2,3.8,1)],.008,WIRE,True)
for i,m in enumerate([IVORY,CYAN,IVORY]):
    vs=[]; fs=[]
    for iz in range(6):
        for ix in range(7): vs.append((-4.45+i*.65+ix*.07,3.8+.025*math.sin(ix+iz*.7),.95-iz*.075))
    for iz in range(5):
        for ix in range(6): a=iz*7+ix; fs.append((a,a+1,a+8,a+7))
    mesh('Tiny laundry cloth',vs,fs,m)
# Sunflowers are actual stalks, leaves, petal heads and seed discs.
active=COL['village']; sv=[]; sf=[]; syv=[]; syf=[]
for ix in range(22):
    for iy in range(12):
        x=-20.4+ix*.29+random.uniform(-.025,.025); y=5.55+iy*.29+random.uniform(-.025,.025); h=random.uniform(.42,.69)
        rod('Sunflower stalk',(x,y,.22),(x+.025,y,.22+h),.012,LEAF,5)
        for dz,side in [(.2,-1),(.34,1)]:
            j=len(sv); sv.extend([(x,y,.22+dz),(x+side*.12,y-.035,.22+dz+.08),(x+side*.22,y,.22+dz+.10),(x+side*.12,y+.035,.22+dz+.08)]); sf.append((j,j+1,j+2,j+3))
        center=Vector((x+.025,y,.22+h)); rod('Sunflower seed centre',center+Vector((0,-.014,0)),center+Vector((0,.014,0)),.05,SEED,12)
        for j in range(10):
            a=j*math.tau/10; u=Vector((math.cos(a),0,math.sin(a))); v=Vector((-math.sin(a),0,math.cos(a)))*.018
            k=len(syv); syv.extend([tuple(center+u*.042),tuple(center+u*.065+v),tuple(center+u*.108),tuple(center+u*.065-v)]); syf.append((k,k+1,k+2,k+3))
mesh('Sunflower broad leaves',sv,sf,LEAF); mesh('Golden sunflower petals',syv,syf,YELLOW)
# Satin ribbon geometry, kept separate for a future trim-path draw.
for o in list(COL['routes'].objects):
    if o.name.startswith('Route '): bpy.data.objects.remove(o,do_unlink=True)
active=COL['routes']
for i,(points,material) in enumerate(zip(new_paths,[PPC,CYAN,ELECTRIC])):
    ribbon=strip_path('Route %d | satin road ribbon'%i,[(x,y,.175) for x,y,z in points],.31,material)
    solid=ribbon.modifiers.new('Satin tape thickness','SOLIDIFY'); solid.thickness=.008
scene['route_paths']=json.dumps(new_paths)
# Put the three route trucks at distinct visible points for the work chapter.
route_paths=json.loads(scene['route_paths'])
def path_at(points,t):
    ps=[Vector(p) for p in points]; lens=[(b-a).length for a,b in zip(ps,ps[1:])]; d=t*sum(lens)
    for a,b,le in zip(ps,ps[1:],lens):
        if d<=le: return a.lerp(b,d/le),b-a
        d-=le
    return ps[-1],ps[-1]-ps[-2]
truck_anchors={}
for i,t in enumerate([.33,.38,.42]):
    pos,di=path_at(route_paths[i],t); pos.z-=.075; o=bpy.data.objects['Moving route truck %d'%i]; o.location=pos; o.rotation_euler.z=math.atan2(di.y,di.x); truck_anchors['truck_'+str(i+1)]=tuple(pos+Vector((0,0,.75)))
# The existing depot is one coherent small campus at the top-left of the village.
bpy.context.view_layer.update()
depot_T=Matrix.Translation(Vector((-4.5,3.2,0)))@Matrix.Rotation(.10,4,'Z')@Matrix.Diagonal((.72,.72,.72,1))@Matrix.Translation(Vector((15,3,0)))
for ob in list(COL['depot'].objects)+list(COL['parked'].objects):
    if ob.parent is None: ob.matrix_world=depot_T@ob.matrix_world
for ob in COL['details'].objects:
    if ob.parent is None and (ob.name.startswith(('Depot crew','Coffee thermos','Dog'))): ob.matrix_world=depot_T@ob.matrix_world
field_T=Matrix.Translation(Vector((3.8,-2,-.10)))@Matrix.Diagonal((.65,.65,1,1))@Matrix.Translation(Vector((17,-7.2,0)))
for ob in COL['village'].objects:
    if ob.name.startswith(('Sunflower','Golden sunflower')): ob.matrix_world=field_T@ob.matrix_world
for ob in COL['parked'].objects:
    if ob.parent is None and ob.type=='EMPTY': ob.location.z-=.03
# A cat on a tile ridge, exposed bricks, rain gutters and small foundations reward close inspection.
active=COL['details']
sphere('Ginger roof cat body',(-5.1,-3.4,2.02),(.09,.04,.055),WOOD)
sphere('Ginger roof cat head',(-5.0,-3.4,2.10),(.043,.035,.04),WOOD)
curve('Cat curled tail',[(-5.2,-3.4,2.02),(-5.26,-3.4,2.09),(-5.25,-3.35,2.15)],.016,WOOD,True)
for hx,hy in [(a,b*.72) for a,b in houses[:27]]:
    for j in range(random.randint(3,7)):
        box('Exposed old brick',(hx-.5+(j%3)*.13,hy-.65,.25+(j//3)*.06),(.12,.025,.055),ROOF,.006)
    if random.random()<.7: rod('Weathered rain downpipe',(hx+.61,hy-.62,.24),(hx+.61,hy-.62,1.26),.021,CONCRETE,8)
# The dawn convoy follows the same physical winding main road.
for i in range(5):
    position,direction=path_at(new_paths[0],.12+i*.17); position.z-=.075
    ob=bpy.data.objects['Dawn convoy %d'%i]; ob.location=position; ob.rotation_euler.z=math.atan2(direction.y,direction.x)
bpy.context.view_layer.update()
pose_anchors={}
for pose,roots in {'parked':['Parked bucket truck %d'%i for i in range(5)],'dispatch':['Dawn convoy %d'%i for i in range(5)],'routes':['Moving route truck %d'%i for i in range(3)],'storm':['Storm response truck','Parked bucket truck 1','Parked bucket truck 2']}.items():
    pose_anchors[pose]=[]
    for root_name in roots:
        root=bpy.data.objects[root_name]; point=root.matrix_world@Vector((0,0,1.50)); center=root.matrix_world.translation
        pose_anchors[pose].append({'point':list(point),'center':[center.x,center.y]})
scene['truck_pose_anchors']=json.dumps(pose_anchors)
# Terrain is a proper closed spherical surface at factor one and a grid at factor zero.
active=COL['terrain']; nx,ny=240,150; gv=[]; gf=[]; density=[]; earth_masks=[]
flat_houses=[(x,y*.72) for x,y in houses]
for j in range(ny+1):
    rr=math.pi*R*j/ny
    for i in range(nx+1):
        angle=math.tau*i/nx; x,y=rr*math.cos(angle),rr*math.sin(angle)
        road_d=min(math.hypot(x-px,y-py) for path in new_paths for px,py,pz in path)
        in_house=any(abs(x-a)<1.0 and abs(y-b)<.85 for a,b in flat_houses)
        depot=-8.2<x<-.9 and 1.1<y<5.2; field=1.5<x<6.2 and -3.3<y<-.7
        side=max(0,min(1,(rr/R-.85)/.65)); coarse=(math.sin(x*1.7)*math.sin(y*2.1)+.4*math.sin(x*4.1+y*2.8))
        z=.115+coarse*(.055 if rr<11 else .24)+side*.10*math.sin(x*3.7-y*.8)
        if road_d<.7 or in_house or depot or field: z=.115+.005*math.sin(x*3)*math.sin(y*3)
        gv.append((x,y,z)); earth_masks.append(side)
        weight=max(0,min(1,(road_d-.42)/.35))
        if in_house or depot or field: weight=0
        density.append(weight*random.uniform(.5,1)*(1-.78*side))
for j in range(ny):
    for i in range(nx): a=j*(nx+1)+i; gf.append((a,a+nx+1,a+nx+2,a+1))
terrain=mesh('Living moss and earth sphere',gv,gf,GRASS)
for f in terrain.data.polygons: f.use_smooth=True
# Small irregular earth and moss clumps break the perfect spherical silhouette.
active=COL['terrain']; cv=[]; cf=[]
bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1); bm.verts.ensure_lookup_table(); bm.verts.index_update(); template=[v.co.copy() for v in bm.verts]; tf=[tuple(v.index for v in f.verts) for f in bm.faces]; bm.free()
for i in range(12000):
    rr=R*math.acos(random.uniform(-1,1)); aa=random.uniform(0,math.tau); x,y=rr*math.cos(aa),rr*math.sin(aa)
    in_village=abs(x)<22 and abs(y)<9.6
    if any((x-px)**2+(y-py)**2<.65**2 for path in new_paths for px,py,pz in path): continue
    if any(abs(x-a)<1.1 and abs(y-b)<.9 for a,b in flat_houses): continue
    if (-8.2<x<-.9 and 1.1<y<5.2) or (1.5<x<6.2 and -3.3<y<-.7): continue
    rr=random.uniform(.012,.072); ax,ay,az=[random.uniform(.55,1.4) for _ in range(3)]; j=len(cv); cv.extend([tuple(Vector((x,y,.14))+Vector((v.x*rr*ax,v.y*rr*ay,v.z*rr*az*.7))) for v in template]); cf.extend([tuple(j+k for k in f) for f in tf])
clumps=mesh('Hand-placed earthy moss granules',cv,cf,GRASS)
clumps.data.materials.append(STONE)
for i,f in enumerate(clumps.data.polygons): f.use_smooth=(i//len(tf))%5>=1; f.material_index=1 if (i//len(tf))%5<1 else 0
# Loose aggregate and wheel ruts break the constructed edges of the rural lanes.
active=COL['terrain']; pv=[]; pf=[]
for path in new_paths:
    for i in range(1000):
        k=random.randrange(len(path)-1); aa,bb=Vector(path[k]),Vector(path[k+1]); pp=aa.lerp(bb,random.random()); di=(bb-aa).normalized(); pp+=Vector((-di.y,di.x,0))*random.uniform(-.67,.67); pp.z=.14
        size=random.uniform(.008,.033); j=len(pv); pv.extend([tuple(pp+Vector((v.x*size,v.y*size,v.z*size*.55))) for v in template]); pf.extend([tuple(j+q for q in f) for f in tf])
mesh('Individual loose roadside gravel',pv,pf,GRAVEL)
for node in CLOUD.node_tree.nodes:
    if node.type=='BUMP': node.inputs['Distance'].default_value=.0005; node.inputs['Strength'].default_value=.6
# Fine cotton fibres and individual clear droplets are retained for the storm.
active=COL['storm']
for i in range(75):
    x=random.uniform(4.2,9.8); y=random.uniform(1.0,2.5); z=random.uniform(2.1,6.2)
    sphere('Clear fishing-line rain droplet',(x,y,z),(.018,.018,.033),RAIN)
# The miniature's fences follow the curved ground, one real picket at a time.
for ob in list(COL['village'].objects):
    if ob.name.startswith(('Yard side fence','Front fence','Fence post')): bpy.data.objects.remove(ob,do_unlink=True)
active=COL['village']
for hx,hy in [(x,y*.72) for x,y in houses[:27]]:
    lon=hx/R; lat=hy/R+LAT; ex=Vector((math.cos(lon),math.sin(lon),0)); ey=Vector((-math.sin(lat)*math.sin(lon),math.sin(lat)*math.cos(lon),math.cos(lat)))
    angle=math.atan2(-hx,hy+.4)+.13*math.sin(hx*7+hy*3)
    def fp(x,y,z): return (hx+math.cos(angle)*x-math.sin(angle)*y,hy+math.sin(angle)*x+math.cos(angle)*y,z)
    for j in range(15):
        xx=-1.05+j*.15
        if abs(xx)<.24: continue
        aa=fp(xx,-1.07,.16); bb=fp(xx,-1.07,.48)
        rod('Crafted fence picket',aa,bb,.021,WOOD,8)
    for side in [-1,1]:
        for zz in [.25,.35]: curve('Crafted fence curved rail',[fp(side*(.28+j*.12),-1.07,zz) for j in range(7)],.014,WOOD)
# Move the cotton cloud above the visible village; parallel rain stops inside the terrain.
bpy.context.view_layer.update()
cloud_T=Matrix.Translation(Vector((-7,-4.44,-4.7)))
for ob in COL['storm'].objects:
    if ob.parent is None and any(k in ob.name.lower() for k in ['cloud','rain','filament','fishing-line']): ob.matrix_world=cloud_T@ob.matrix_world
# Actual curled cotton strands supplement the particle hairs at the cloud silhouette.
active=COL['storm']; cloud=bpy.data.objects['Unified sculpted felt storm cloud']
cloud.modifiers.get('Subtle felt surface').strength=.18
bpy.context.view_layer.update(); evaluated=cloud.evaluated_get(bpy.context.evaluated_depsgraph_get()); cloud_mesh=evaluated.to_mesh()
cotton_mat=paint('Loose warm grey cotton fibres','C4C3BF',1)
fibres=bpy.data.curves.new('Individually curled cotton fibres','CURVE'); fibres.dimensions='3D'; fibres.resolution_u=1; fibres.bevel_depth=.0010; fibres.bevel_resolution=0
for i in range(7000):
    vertex=random.choice(cloud_mesh.vertices); root=cloud.matrix_world@vertex.co; normal=(cloud.matrix_world.to_3x3()@vertex.normal).normalized(); tangent=normal.cross(Vector((.31,.72,.2))).normalized(); sideways=normal.cross(tangent)
    length=random.uniform(.035,.16); spline=fibres.splines.new('POLY'); spline.points.add(5); phase=random.uniform(0,math.tau)
    for j,point in enumerate(spline.points):
        t=j/5; pp=root+normal*length*t+tangent*(.018*math.sin(t*5+phase))+sideways*(.015*math.cos(t*6+phase)); point.co=(*pp,1); point.radius=1-t*.85
evaluated.to_mesh_clear(); fibre_obj=bpy.data.objects.new('Cloud loose curled cotton strands',fibres); active.objects.link(fibre_obj); fibres.materials.append(cotton_mat)
# Snapshot and combine the evaluated geometry before the shared morph. Textures keep flat UVs.
print('PLANET_GEOMETRY_READY',len(bpy.data.objects),flush=True)
bpy.context.view_layer.update(); deps=bpy.context.evaluated_depsgraph_get()
buckets={}; originals=[]; cloud_obj=bpy.data.objects.get('Unified sculpted felt storm cloud')
for cname in ['village','depot','storm','parked','dispatch','routes','foliage','details','terrain']:
    for o in list(COL[cname].objects):
        if o.type not in ['MESH','CURVE']: continue
        root_for_bucket=o
        while root_for_bucket.parent is not None: root_for_bucket=root_for_bucket.parent
        special='cloud' if o==cloud_obj else 'terrain' if o==terrain else root_for_bucket.name if cname=='parked' else ''
        key=(cname,special); b=buckets.setdefault(key,{'v':[],'f':[],'mi':[],'smooth':[],'uv':[],'materials':[],'density':density if o==terrain else None,'centers':[]})
        me=bpy.data.meshes.new_from_object(o.evaluated_get(deps)); mw=o.matrix_world
        offset=len(b['v']); local=[v.co.copy() for v in me.vertices]
        coords=[mw@v for v in local]
        if cname=='foliage' or o.name.startswith(('Walnut trunk','Walnut branch')):
            for pp in coords: pp.z-=.07
        if 'depot gravel yard' in o.name.lower():
            for pp in coords: pp.z-=.01
        root=o
        while root.parent is not None: root=root.parent
        rigid=None; n=o.name.lower(); center=mw.translation
        if 'planet_center' in o: rigid=tuple(o['planet_center'])
        elif root.type=='EMPTY' and root.name.startswith('Dropping pin'):
            cc=sum(coords,Vector())/len(coords); rigid=min(flat_houses,key=lambda q:(q[0]-cc.x)**2+(q[1]-cc.y)**2)
        elif root.type=='EMPTY' and root.name!='Actual hot-roof panel assembly': rigid=(root.location.x,root.location.y)
        elif ('depot' in n or 'workshop' in n or 'stored repair' in n) and not any(k in n for k in ['raised yard','fence','parking','gravel yard','service pad']): rigid=(-6.05,4.25)
        elif cname=='storm' and (o==cloud_obj or any(k in n for k in ['rain','cloud','filament','fishing-line'])): rigid=(0,-3)
        elif any(k in n for k in ['snapped concrete','broken pole','fallen crossarm','loose fallen']): rigid=(2.4,.5)
        elif 'crafted fence picket' in n: rigid=(center.x,center.y)
        elif 'crafted fence' in n: rigid=None
        elif 'walnut trunk' in n: rigid=(center.x,center.y)
        elif 'dog' in n:
            dc=depot_T@Vector((-16.8,-4.8,0)); rigid=(dc.x,dc.y)
        elif 'laundry' in n: rigid=(-3.4,3.8)
        elif 'meter' in n or 'tampering' in n: rigid=(-6.4,-.6)
        elif root.name=='Actual hot-roof panel assembly': rigid=(-5.1,-3.4)
        elif cname=='details' and any(k in n for k in ['exposed old brick','weathered rain downpipe','ginger roof cat','cat curled tail']):
            cc=sum(coords,Vector())/len(coords); rigid=min(flat_houses,key=lambda q:(q[0]-cc.x)**2+(q[1]-cc.y)**2)
        elif cname=='village' and not any(k in n for k in ['sunflower','road','lane','barrel roof tiles']):
            cc=sum(coords,Vector())/len(coords)
            near=min(flat_houses,key=lambda q:(q[0]-cc.x)**2+(q[1]-cc.y)**2)
            if (near[0]-cc.x)**2+(near[1]-cc.y)**2<4: rigid=near
        if 'wire_line' in o:
            x1,y1,x2,y2,off=o['wire_line']; dx,dy=x2-x1,y2-y1; ll=dx*dx+dy*dy; centers=[]
            for point in coords:
                t=max(0,min(1,((point.x-off-x1)*dx+(point.y-y1)*dy)/ll)); centers.append((x1+dx*t,y1+dy*t))
        elif o.name=='Translucent individual walnut leaf clusters': centers=leaf_attach
        elif 'barrel roof tiles' in n: centers=tile_attach
        else: centers=[rigid]*len(coords)
        b['v'].extend([tuple(v) for v in coords]); b['centers'].extend(centers)
        mids=[]
        for m in me.materials:
            if m not in b['materials']: b['materials'].append(m)
            mids.append(b['materials'].index(m))
        phase=random.uniform(0,10)
        for poly in me.polygons:
            ids=tuple(poly.vertices); b['f'].append(tuple(v+offset for v in ids)); b['mi'].append(mids[poly.material_index] if mids else 0); b['smooth'].append(poly.use_smooth)
            normal=poly.normal; axis=max(range(3),key=lambda a:abs(normal[a])); uv=[]
            for vi in ids:
                co=local[vi]; a,bb=((co.y,co.z) if axis==0 else (co.x,co.z) if axis==1 else (co.x,co.y)); uv.append((a+phase,bb+phase*.7))
            b['uv'].extend(uv)
        bpy.data.meshes.remove(me); originals.append(o)
for o in originals: bpy.data.objects.remove(o,do_unlink=True)
for cname in ['village','depot','storm','parked','dispatch','routes','foliage','details']:
    for o in list(COL[cname].objects):
        if o.type=='EMPTY': bpy.data.objects.remove(o,do_unlink=True)

def warp(p):
    x,y,z=p; return Vector((x+.10*math.sin(y*.4),y+.10*math.sin(x*.27),z))
def sphere_point(p): return azimuthal(p,R,1)
def rigid_point(p,center): return azimuthal_rigid(p,center,R,1)
active=COL['anchors']; control=group_new('Planet_Control'); control['flat_to_planet']=1.; control.id_properties_ui('flat_to_planet').update(min=0,max=1)
scene['model_scale']=S; scene['planet_radius']=R; scene['latitude_offset']=0.; scene['planet_pipeline']=True
roll_group,roll_identifier=make_roll_group(R*S)
morph_objects=[]; terrain_new=None; cloud_new=None
for (cname,special),b in buckets.items():
    active=COL[cname]; name='Planet_'+cname+('_'+special if special else '')
    flat=[]; wrapped=[]; centers=[]; heights=[]; crust=[]
    for v,center in zip(b['v'],b['centers']):
        pp=warp(v)
        if center is not None:
            pp.z-=.10; cc=warp((*center,0)); cv=(cc.x*S,cc.y*S,1.)
            # Different houses face the irregular village lanes, rather than an identical camera-facing grid.
            if any((center[0]-hx)**2+(center[1]-hy)**2<.4**2 for hx,hy in flat_houses):
                yaw=math.atan2(-center[0],center[1]+.4)+.13*math.sin(center[0]*7+center[1]*3)
                dx,dy=pp.x-cc.x,pp.y-cc.y; pp.x=cc.x+math.cos(yaw)*dx-math.sin(yaw)*dy; pp.y=cc.y+math.sin(yaw)*dx+math.cos(yaw)*dy
            qq=rigid_point(pp,(cc.x,cc.y))
        else: cv=(0,0,0); qq=sphere_point(pp)
        flat.append((pp.x*S,pp.y*S,(R+pp.z)*S)); wrapped.append(tuple(qq*S)); centers.append(cv); heights.append(pp.z*S); crust.append(max(0,min(1,(math.hypot(pp.x,pp.y)/R-.85)/.65)))
    hair_emitter=special in ['terrain','cloud']
    o=mesh(name,wrapped if hair_emitter else flat,b['f'],b['materials'][0])
    for m in b['materials'][1:]: o.data.materials.append(m)
    for face,mi,sm in zip(o.data.polygons,b['mi'],b['smooth']): face.material_index=mi; face.use_smooth=sm
    uv=o.data.uv_layers.new(name='Scanned material UVs')
    for loop,coord in zip(uv.data,b['uv']): loop.uv=coord
    attr=o.data.attributes.new('model_height','FLOAT','POINT'); attr.data.foreach_set('value',heights)
    attr=o.data.attributes.new('earth_crust','FLOAT','POINT'); attr.data.foreach_set('value',crust)
    attach_roll(o,roll_group,roll_identifier,control,flat,centers); morph_objects.append(o)
    if special=='terrain': terrain_new=o
    if special=='cloud': cloud_new=o
# Real legacy hair particle flock follows the deformed emitter's normals and roots.
def flock(o,name,count,length,matl,children=2):
    bpy.context.view_layer.objects.active=o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.particle_system_add(); ps=o.particle_systems[-1]; settings=ps.settings; settings.name=name; settings.type='HAIR'; settings.count=count; settings.hair_length=length; settings.hair_step=2
    settings.child_type='INTERPOLATED'; settings.child_percent=children; settings.rendered_child_count=children; settings.use_advanced_hair=True
    settings.root_radius=.00010; settings.tip_radius=.000025; settings.radius_scale=1
    settings.length_random=.65; settings.roughness_1=.0004; settings.roughness_2=.0002
    o.data.materials.append(matl); settings.material=len(o.data.materials)
    settings.use_modifier_stack=False
    return ps
vg=terrain_new.vertex_groups.new(name='Flock away from roads and houses')
for i,weight in enumerate(density):
    if weight: vg.add([i],weight,'REPLACE')
bpy.context.view_layer.update()
ps=flock(terrain_new,'Real fine flock grass and moss',360000,.0038,HAIR,6); ps.vertex_group_density=vg.name
# The cotton fibres are the explicit curled curves above. Legacy hair on this
# rigid GN emitter creates a second rest-position silhouette in Blender 5.2.
# Extra material detail on the earth's edge, without a smooth CGI globe silhouette.
tex=bpy.data.textures.new('Earth microrelief',type='CLOUDS'); tex.noise_scale=.026; tex.noise_depth=2
mod=terrain_new.modifiers.new('Hand-shaped uneven earth','DISPLACE'); mod.texture=tex; mod.strength=.0006; mod.mid_level=.5
# All tracked points are driven by the same control, not hand-entered screen positions.
anchor_flat={'fallen_pole':(1.2,-.36,1.05),'meter':(-6.4,-1.35,.86),'hot_roof':(-5.44,-3.4,1.85),'depot':(-6.05,4.05,1.1),'unsure_house':(6.3,.4,1.8),**truck_anchors}
scene['anchor_flat']=json.dumps(anchor_flat)
anchor_centers={'fallen_pole':(2.4,.5),'meter':(-6.4,-.6),'hot_roof':(-5.1,-3.4),'depot':(-6.05,4.25),'unsure_house':(6.3,.4)}
scene['anchor_centers']=json.dumps(anchor_centers)
for name,p0 in anchor_flat.items():
    active=COL['anchors']; pp=warp(p0); pp.z-=.1; cx,cy=anchor_centers.get(name,(p0[0],p0[1])); cc=warp((cx,cy,0))
    if name in ['meter','hot_roof','unsure_house']:
        yaw=math.atan2(-cx,cy+.4)+.13*math.sin(cx*7+cy*3); dx,dy=pp.x-cc.x,pp.y-cc.y; pp.x=cc.x+math.cos(yaw)*dx-math.sin(yaw)*dy; pp.y=cc.y+math.sin(yaw)*dx+math.cos(yaw)*dy
    o=mesh(name,[(pp.x*S,pp.y*S,(R+pp.z)*S)],[],IVORY)
    attach_roll(o,roll_group,roll_identifier,control,[(pp.x*S,pp.y*S,(R+pp.z)*S)],[(cc.x*S,cc.y*S,1.)])
# Clean flat PPC map overlay, reserved for the 9.8-second interface hand-off.
active=COL['map_graphic']; mg=box('PPC flat map ground',(0,0,-.001),(2.8,1.5,.002),NAVY,.004)
for x,y in flat_houses: box('White house footprint',(x*S,y*S,.001),(.058,.058,.002),IVORY,.003)
for path in new_paths:
    strip_path('Cyan map road',[(x*S,y*S,.002) for x,y,z in path],.014,CYAN)
for i,(x,y) in enumerate([(-6.4,-.6),(-5.1,-3.4),(6.3,.4),(-6.05,4.25)]): sphere('Flat map anchor pin',(x*S,y*S,.008),(.008,.008,.005),[PPC,CYAN,ELECTRIC,PPC][i%4])
box('Depot white footprint',(-6.05*S,4.25*S,.001),(.14,.06,.002),IVORY,.003)
for i,data in enumerate(pose_anchors['parked'][:3]):
    xy=warp(data['point']); box('Orange depot truck marker',(xy.x*S,xy.y*S,.004),(.018,.034,.003),PPC,.002)
# Navy camera background, studio HDRI for illumination/reflections only.
world=bpy.data.worlds.new('PPC navy void with Poly Haven studio illumination'); scene.world=world; world.use_nodes=True; nt=world.node_tree; nt.nodes.clear()
out=nt.nodes.new('ShaderNodeOutputWorld'); mix=nt.nodes.new('ShaderNodeMixShader'); path=nt.nodes.new('ShaderNodeLightPath')
env=nt.nodes.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load(str(ROOT/'assets'/A['studio_small_03']['files']['hdri']['local']),check_existing=True)
bg=nt.nodes.new('ShaderNodeBackground'); bg.name='HDRI illumination'; bg.inputs['Strength'].default_value=.24; nt.links.new(env.outputs[0],bg.inputs['Color'])
navy=nt.nodes.new('ShaderNodeBackground'); navy.name='PPC navy camera background'; navy.inputs['Color'].default_value=(*color('000F1E'),1); navy.inputs['Strength'].default_value=3
nt.links.new(path.outputs['Is Camera Ray'],mix.inputs[0]); nt.links.new(bg.outputs[0],mix.inputs[1]); nt.links.new(navy.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],out.inputs[0])
active=COL['lights']
keylight=area('Warm museum studio key',(1.25,-1.25,1.7),(0,0,.1),125,1.1,(1,.83,.63)); keylight.data.energy=125
fill=area('Cool silk fill',(-1.2,-.6,.8),(0,0,.15),45,1.6,(.55,.74,1)); fill.data.energy=45
rim=area('Fine warm edge',(0,.8,1.4),(0,0,0),65,.8,(1,.85,.66)); rim.data.energy=65
sun_data=bpy.data.lights.new('Daybreak moving sun','SUN'); sun_data.energy=2.8; sun_data.angle=.07; sun_data.color=(1,.44,.12); sun=bpy.data.objects.new('Daybreak moving sun',sun_data); active.objects.link(sun); sun.rotation_euler=(.9,-.7,-.6)
for name in ['fallen_pole','meter','hot_roof']:
    bpy.context.view_layer.update(); ao=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get()); sp=ao.matrix_world@ao.data.vertices[0].co; normal=sp.normalized(); d=bpy.data.lights.new('Problem spot '+name,'SPOT'); d.energy=.35; d.spot_size=.4; d.spot_blend=.55; d.shadow_soft_size=.005; d.color={'fallen_pole':(1,.6,.3),'meter':(.25,.75,1),'hot_roof':(.35,.5,1)}[name]
    ob=bpy.data.objects.new(d.name,d); active.objects.link(ob); ob.location=sp+normal*.20; ob.rotation_euler=(sp-ob.location).to_track_quat('-Z','Y').to_euler()
# Tiny garage practicals use actual light sources, without bloom.
for i,x in enumerate([-18.5,-17,-15.5]):
    pp=warp(depot_T@Vector((x,-1.25,1.7))); pp.z-=.1; pos=rigid_point(pp,(-6.05,4.25))*S; d=bpy.data.lights.new('Depot practical %d'%i,'POINT'); d.energy=.15; d.color=(1,.56,.22); d.shadow_soft_size=.012
    ob=bpy.data.objects.new(d.name,d); active.objects.link(ob); ob.location=pos
active=COL['studio']; sunball=sphere('Orange sunrise disc',(0,.8,.1),(.11,.11,.11),PPC)
p=sunball.data.materials[0].node_tree.nodes.get('Principled BSDF'); # A separate non-halo sunrise sphere.
SUNMAT=paint('PPC orange sun disc','FA4616',1); p=SUNMAT.node_tree.nodes.get('Principled BSDF'); p.inputs['Emission Color'].default_value=(*color('FA4616'),1); p.inputs['Emission Strength'].default_value=.8; sunball.data.materials.clear(); sunball.data.materials.append(SUNMAT)
active=COL['hero_camera']; cam=camera('Planet hero camera',(-1.15,-1.65,1.05),(0,0,.08),1.5,(0,0),4)
cam.data.type='PERSP'; cam.data.lens=65; cam.data.clip_start=.002; cam.data.clip_end=100; cam.data.dof.aperture_fstop=4; cam.data.dof.aperture_blades=9; scene.camera=cam
focus=group_new('Photographic focus'); focus.location=(-.1,-.16,.18); cam.data.dof.focus_object=focus
scene.render.engine='CYCLES'; scene.cycles.samples=256; scene.cycles.adaptive_threshold=.01; scene.cycles.use_denoising=True; scene.cycles.device='GPU'; scene.cycles.max_bounces=8; scene.cycles.transmission_bounces=6
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=0
scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100; scene.render.film_transparent=False; scene.render.use_persistent_data=True
scene.frame_start=1; scene.frame_end=900; scene.render.fps=30
for cname in ['storm','parked','dispatch','routes','map_graphic']: COL[cname].hide_render=cname!='routes'
for o in COL['lights'].objects:
    if o.name.startswith('Problem spot') or o.name=='Daybreak moving sun': o.hide_render=True
sunball.hide_render=True
scene['asset_manifest']=json.dumps(ASSETS); scene['morph_method']='Exact native azimuthal Geometry Nodes rolling field; Shared lerp of flat and sphere; buildings and vehicles use rigid radial tangent frames; ground/roads use per-vertex wrapping. All keys driven by Planet_Control.flat_to_planet. Hair roots follow deformed emitter.'
# Pack all external images into the native Blender source for dependable hand-off.
exec(compile((ROOT/'scripts'/'prepare_damage.py').read_text(),str(ROOT/'scripts'/'prepare_damage.py'),'exec'),globals())
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'daybreak_planet.blend'))
print('PLANET_BUILD_DONE '+json.dumps({'objects':len(bpy.data.objects),'morph_objects':len(morph_objects),'assets':len(ASSETS),'radius_metres':R*S,'hairs':360000,'children_per_parent':6}),flush=True)
