"""Daybreak, deterministic architectural model. Run with Blender 5.2.1 -b -P."""
import bpy, bmesh, math, random, json, sys, time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SEED=270611
random.seed(SEED)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
COL={}
def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); COL[name]=c; return c
for n in ['stage','village','depot','storm','parked','dispatch','routes','problems','light_storm','light_where','light_problems','light_map','light_dawn','cameras']: collection(n)
active=COL['village']
def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    active.objects.link(o); return o

def linear(x): return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
def mat(name,h,rough=.85,metal=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); rgb=tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))
    p.inputs['Base Color'].default_value=(*rgb,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    if not metal: p.inputs['Specular IOR Level'].default_value=.18
    if name in ['Warm white card | F3F1EC','White resin']:
        ao=m.node_tree.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=.8; ao.samples=4
        mix=m.node_tree.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=.65; mix.inputs[1].default_value=(*rgb,1)
        m.node_tree.links.new(ao.outputs['Color'],mix.inputs[2]); m.node_tree.links.new(mix.outputs[0],p.inputs['Base Color'])
    return m
WHITE=mat('Warm white card | F3F1EC','F3F1EC'); EDGE=mat('White resin','FAF9F5',.75)
TABLE=mat('Seamless warm grey | E7E3DC','E7E3DC',.9)
ORANGE=mat('Safety orange | FF5B1A','FF5B1A',.66); BLUE=mat('Cobalt | 1E4FD8','1E4FD8',.72); GREEN=mat('Green | 1FA35B','1FA35B',.72)
WIRE=mat('Graphite power wire','666562',.9); CLOUD=mat('Warm grey felt | 8E8C88','8E8C88',1)
GLASS=mat('Ivory frosted cab glazing','DDDCD5',.23); SOLAR=mat('Solar | 1C2A4A','1C2A4A',.24,.25); BRASS=mat('Polished brass sun','C5A355',.21,.8)
RAIN=mat('Pale translucent rain','E7E9E8',.28); RAIN.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.35
# Felt stays restrained at a distance, resolves into fine fibres in the close shot.
nt=CLOUD.node_tree; p=nt.nodes.get('Principled BSDF'); p.inputs['Sheen Weight'].default_value=.35
noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=95; noise.inputs['Detail'].default_value=2
bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.26; bump.inputs['Distance'].default_value=.035
nt.links.new(noise.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])

def finish(o,name,m):
    o.name=name; link(o)
    if m: o.data.materials.append(m)
    return o

def box(name,loc,size,m=WHITE,bevel=.018,rot=None):
    sx,sy,sz=[v/2 for v in size]
    vs=[(a*sx,b*sy,c*sz) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,vs,[tuple(reversed(f)) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]],m); o.location=loc
    if bevel:
        mod=o.modifiers.new('Laser-cut edge','BEVEL'); mod.width=bevel; mod.segments=2
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    if rot: o.rotation_euler=rot
    return o

def mesh(name,verts,faces,m=WHITE):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); active.objects.link(o); me.materials.append(m); return o

def rod(name,a,b,r=.025,m=WHITE,verts=10):
    a,b=Vector(a),Vector(b); d=b-a
    vs=[(r*math.cos(2*math.pi*i/verts),r*math.sin(2*math.pi*i/verts),z) for z in [-d.length/2,d.length/2] for i in range(verts)]
    fs=[tuple(reversed(range(verts))),tuple(range(verts,verts*2))]+[(i,(i+1)%verts,(i+1)%verts+verts,i+verts) for i in range(verts)]
    o=mesh(name,vs,fs,m); o.location=(a+b)/2; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def sphere(name,loc,scale,m=WHITE,faceted=False):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=2 if faceted else 3,radius=1); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); active.objects.link(o); me.materials.append(m); o.location=loc; o.scale=scale
    if not faceted:
        for p in o.data.polygons: p.use_smooth=True
    return o

def curve(name,pts,r,m,bezier=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=12; cu.bevel_depth=r; cu.bevel_resolution=3
    if bezier:
        sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
        for p,co in zip(sp.bezier_points,pts): p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
    else:
        sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
        for p,co in zip(sp.points,pts): p.co=(*co,1)
    o=bpy.data.objects.new(name,cu); active.objects.link(o); cu.materials.append(m); return o

def group_new(name):
    o=bpy.data.objects.new(name,None); active.objects.link(o); return o

def parent_new(parent,before):
    for o in set(active.objects)-before:
        if o!=parent: o.parent=parent

def roof(name,x,y,z,w,d,rise,m=WHITE):
    verts=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x,y-d/2,z+rise),(x-w/2,y+d/2,z),(x+w/2,y+d/2,z),(x,y+d/2,z+rise)]
    mesh(name+' gable',verts,[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(2,1,4,5)],m)
    a=math.atan2(rise,w/2); slope=math.hypot(w/2,rise)
    for side in [-1,1]:
        box(name+' card roof', (x+side*w/4,y,z+rise/2+.03),(slope+.13,d+.15,.055),EDGE,.012,(0,side*a,0))
    rod(name+' ridge',(x,y-d/2-.09,z+rise+.055),(x,y+d/2+.09,z+rise+.055),.027,EDGE)

def front_wall(name,x,y,z,w,h,windows):
    # Actual open wall cells, with white backing 40 mm behind their edges.
    holes=[]
    for xx,ww,zz,hh in windows: holes.append((xx-ww/2,xx+ww/2,zz,zz+hh))
    xs=sorted(set([-w/2,w/2]+[v for a,b,c,d in holes for v in [a,b]])); zs=sorted(set([0,h]+[v for a,b,c,d in holes for v in [c,d]]))
    vs=[]; fs=[]
    for a,b in zip(xs,xs[1:]):
        for c,d in zip(zs,zs[1:]):
            mx,mz=(a+b)/2,(c+d)/2
            if any(A<mx<B and C<mz<D for A,B,C,D in holes): continue
            i=len(vs); vs.extend([(x+a,y,z+c),(x+b,y,z+c),(x+b,y,z+d),(x+a,y,z+d)])
            fs.append((i+3,i+2,i+1,i))
    o=mesh(name,vs,fs); so=o.modifiers.new('Wall thickness','SOLIDIFY'); so.thickness=.045
    for a,b,c,d in holes:
        box('Recess back',(x+(a+b)/2,y+.055,z+(c+d)/2),(b-a,.015,d-c),WHITE,.002)
        if d-c<.65:
            box('Fine window mullion',(x+(a+b)/2,y-.008,z+(c+d)/2),(.023,.045,d-c),EDGE,.002)
            box('Fine window crossbar',(x+(a+b)/2,y-.01,z+(c+d)/2),(b-a,.045,.021),EDGE,.002)
        box('White sill',(x+(a+b)/2,y-.035,z+c),(b-a+.06,.12,.035),EDGE,.005)

def house(x,y,w=1.55,d=1.75,h=1.05,annex=False,z=.29):
    front_wall('Cut-card facade',x,y-d/2,z,w,h,[(-w*.27,.28,.42,.37),(w*.27,.28,.42,.37),(0,.28,0,.68)])
    box('House back',(x,y+d/2,z+h/2),(w,.06,h));
    for side in [-1,1]:
        box('House side',(x+side*w/2,y,z+h/2),(.055,d,h))
        for yy in [-.4,.35]:
            # Raised frames surround a shallow white inset, no dark painted windows.
            box('Side inset',(x+side*(w/2+.005),y+yy,z+.61),(.018,.32,.36),WHITE,.003)
            for dz in [-.19,.19]: box('Side lintel',(x+side*(w/2+.025),y+yy,z+.61+dz),(.05,.38,.035),EDGE,.003)
            for dy in [-.18,.18]: box('Side jamb',(x+side*(w/2+.025),y+yy+dy,z+.61),(.05,.035,.4),EDGE,.003)
    roof('House',x,y,z+h,w,d,.6)
    box('Chimney',(x+w*.28,y+d*.21,z+h+.42),(.15,.16,.58),WHITE,.008)
    if annex:
        box('L-plan rear wing',(x+w*.72,y+.45,z+.36),(w*.55,d*.7,.72)); roof('Wing',x+w*.72,y+.45,z+.72,w*.55,d*.7,.32)
    # Card boundary and sparse fence stiles.
    for xx in [x-w*.8,x+w*.8]: box('Yard side fence',(xx,y,z+.16),(.027,d+1,.3),WHITE,.002)
    for dx in [-w*.61,w*.61]: box('Front fence',(x+dx,y-d/2-.44,z+.16),(w*.38,.028,.3),WHITE,.002)
    for dx in [-w*.8,-w*.42,w*.42,w*.8]: box('Fence post',(x+dx,y-d/2-.44,z+.19),(.048,.048,.38),EDGE,.004)

def tree(x,y,s=1,z=.29):
    rod('Walnut trunk',(x,y,z),(x,y,z+1.1*s),.055*s)
    for dx,dy,dz,sc in [(-.25,0,1.15,.58),(.25,.06,1.2,.58),(0,-.12,1.58,.61),(0,.23,1.32,.56)]:
        sphere('Faceted white walnut',(x+dx*s,y+dy*s,z+dz*s),(sc*s,sc*.85*s,sc*.95*s),WHITE,True)

def pole(x,y,z=.29):
    rod('Concrete distribution pole',(x,y,z),(x,y,z+2.6),.047)
    box('White crossarm',(x,y,z+2.4),(.88,.075,.075))
    for dx in [-.32,0,.32]:
        rod('Porcelain insulator',(x+dx,y,z+2.4),(x+dx,y,z+2.58),.043,EDGE)

# Table is actual geometry. No horizon, lamps, or photographic rigs enter frame.
active=COL['stage']
# Physical cyclorama, a curved white studio wall with no visible horizon.
profile=[(-200,-.025)]+[(12+12*math.sin(i*math.pi/64),12-12*math.cos(i*math.pi/64)-.025) for i in range(33)]+[(24,100)]
verts=[(x,y,z) for x in [-200,200] for y,z in profile]; n=len(profile)
wall=mesh('Seamless curved studio backdrop',verts,[(i,i+n,i+1+n,i+1) for i in range(n-1)],TABLE)
for f in wall.data.polygons: f.use_smooth=True
normals=[(0,0,1)]+[(0,-math.sin(i*math.pi/64),math.cos(i*math.pi/64)) for i in range(33)]+[(0,-1,0)]
wall.data.normals_split_custom_set([normals[loop.vertex_index % n] for loop in wall.data.loops])
active=COL['village']; box('Thin white base board',(0,0,.09),(44,27,.22),WHITE,.025)
# Streets are the exposed lower board between raised card blocks.
xedges=[(-21.7,-8.65),(-7.35,1.35),(2.65,11.35),(12.65,21.7)]
yedges=[(-13.2,-7.65),(-6.35,-1.6),(1.6,6.35),(7.65,13.2)]
for xa,xb in xedges:
    for ya,yb in yedges: box('Land between recessed roads',((xa+xb)/2,(ya+yb)/2,.24),(xb-xa,yb-ya,.08),WHITE,.018)
# House layout is synthetic, not a survey or operational grid.
houses=[]
xs=[-17.5,-14.6,-11.7,-6.15,-3.35,-.55,4.55,7.35,10,14.35,17.2,20]
for ri,yy in enumerate([-10.1,-3.65,3.65,10.05]):
    for ci,xx in enumerate(xs):
        if ri==1 and xx<-9: continue # Utility yard.
        if ri==3 and xx<-13: continue # Grooved field.
        x=xx+random.uniform(-.14,.14); y=yy+random.uniform(-.2,.2)
        w=random.uniform(1.25,1.55); d=random.uniform(1.5,1.9)
        house(x,y,w,d,random.uniform(.94,1.14),annex=(ri+ci)%7==0); houses.append((x,y))
        if ci%2==0: tree(x+w*.82,y+.8,random.uniform(.6,.8))
# Field board and parallel white ribs leave narrow physical grooves.
box('Sunflower field edge',(-17.1,10.1,.29),(7,5.35,.04),WHITE,.005)
for i in range(44): box('Parallel field groove',(-20.45+i*.153,10.1,.322),(.055,5.05,.025),EDGE,.003)
# Roadside trees and sagging power wires.
for x in [-20,-10,-5,5,15,21]: tree(x,-2.1,.7)
for x in [-19,-13,-7,-1,5,11,17]: pole(x,1.15)
for x1,x2 in zip([-19,-13,-7,-1,5,11],[-13,-7,-1,5,11,17]):
    for dx in [-.32,0,.32]: curve('Suspended dark-grey service wire',[(x1+dx,1.15,2.87),((x1+x2)/2+dx,1.15,2.55),(x2+dx,1.15,2.87)],.009,WIRE,True)
# Utility depot shares the same model and street exit in every beat.
active=COL['depot']; box('Depot cutaway base',(-15,-4.05,.15),(9.8,7.5,.22),WHITE,.025)
box('Depot raised yard',(-15,-4.05,.29),(9.2,6.9,.08),WHITE,.015)
box('Depot shed',(-17,-1.85,1.13),(4.7,1.8,1.65)); roof('Depot shed',-17,-1.85,1.95,4.7,1.8,.5)
for xx in [-18.4,-16.9,-15.4]:
    box('Recessed garage aperture',(xx,-2.77,1.05),(1.17,.03,1.32),WHITE,.004)
    for z in [.46,.72,.98,1.24,1.5]: box('White garage slat',(xx,-2.8,z),(1.12,.028,.018),EDGE,.002)
    for dx in [-.62,.62]: box('Garage jamb',(xx+dx,-2.82,1.05),(.075,.11,1.45),EDGE,.005)
for y in [-7.35,-.6]:
    box('Yard thin fence',(-15,y,.57),(9.25,.035,.5),WHITE,.004)
    for i in range(38): box('Yard fence pale',(-19.5+i*.243,y,.57),(.025,.045,.51),EDGE,.002)
box('Depot western fence',(-19.6,-4.05,.57),(.035,6.7,.5),WHITE,.004)
for yy in [-6.8,-3.8]: tree(-19.1,yy,.72)
for xx in [-18.4,-16.8,-15.2,-13.6,-12]: box('Parking bay card strip',(xx,-5,.34),(.023,2.7,.012),EDGE,.002)

# Precise resin bucket trucks with folded two-link booms, storage doors and hollow buckets.
def truck(name,loc,angle=0):
    before=set(active.objects); p=group_new(name)
    box('Orange utility chassis',(0,0,.36),(1.56,.66,.17),ORANGE,.035)
    box('Cab',( .48,0,.64),(.63,.67,.55),ORANGE,.065)
    box('Bonnet',(.84,0,.49),(.18,.64,.19),ORANGE,.035)
    box('Recessed front glazing',(.802,0,.75),(.018,.53,.24),GLASS,.015)
    for side in [-1,1]:
        box('Cab side glazing',(.46,side*.343,.76),(.37,.015,.24),GLASS,.012)
        box('Side mirror',(.75,side*.405,.72),(.09,.06,.13),ORANGE,.015)
        for xx in [-.55,-.17]:
            box('Truck storage locker',(xx,side*.34,.58),(.32,.025,.28),ORANGE,.012)
            box('Locker handle',(xx,side*.36,.6),(.1,.015,.022),EDGE,.004)
    box('Orange crew bed',(-.36,0,.54),(.94,.68,.28),ORANGE,.025)
    box('Bed resin top',(-.36,0,.7),(.91,.58,.035),ORANGE,.008)
    for x in [-.53,.55]:
        for y in [-.354,.354]:
            rod('White resin tyre',(x,y-.065,.255),(x,y+.065,.255),.185,WHITE,24)
            rod('Wheel hub',(x,y-.072,.255),(x,y+.072,.255),.091,EDGE,20)
    rod('Boom turntable',(-.56,0,.72),(-.56,0,.84),.16,ORANGE,20)
    box('Folded lower boom',(-.12,0,.91),(1.08,.14,.14),ORANGE,.025,(0,-.12,0))
    box('Folded upper boom',(-.13,0,1.09),(1.01,.12,.12),ORANGE,.021,(0,.15,0))
    for xx,zz in [(-.58,.86),(.38,.99),(-.57,1.17)]: rod('White boom pivot',(xx,-.09,zz),(xx,.09,zz),.065,EDGE,16)
    # Empty bucket, not a solid orange cube.
    bx=-.74; bz=1.13
    box('Bucket bottom',(bx,0,bz),(.26,.34,.035),ORANGE,.008)
    for yy in [-.16,.16]: box('Bucket side',(bx,yy,bz+.14),(.27,.035,.28),ORANGE,.012)
    for xx in [bx-.12,bx+.12]: box('Bucket end',(xx,0,bz+.14),(.035,.3,.28),ORANGE,.012)
    box('Front white bumper',(.94,0,.35),(.06,.69,.08),EDGE,.014)
    for yy in [-.23,.23]: box('White headlamp',(.94,yy,.49),(.025,.13,.085),EDGE,.012)
    parent_new(p,before); p.location=loc; p.rotation_euler.z=angle; return p
active=COL['parked']
for i in range(5): truck('Parked bucket truck %d'%i,(-18.1+i*1.5,-5.25,.33),-.88+(.07 if i%2 else -.03))
active=COL['dispatch']
for i in range(5): truck('Dawn convoy %d'%i,(-8.2+i*3.55,.9,.22),0)
# Storm is removable staging of the same village, with a road obstruction.
active=COL['storm']
truck('Storm response truck',(2,-2.4,.22),math.pi/2)
rod('Broken pole stump',(3.6,1.3,.28),(3.6,1.3,.83),.06)
rod('Snapped concrete pole',(3.6,1.3,.81),(2.1,-.5,1.65),.055)
rod('Fallen crossarm',(1.6,-.5,1.65),(2.7,-.5,1.65),.042)
for i in [-1,0,1]: curve('Loose fallen power wire',[(2.1+i*.18,-.5,1.65),(1.8+i*.4,-1.2,.26),(2.5+i*.4,-1.4,.25),(3+i*.2,-.9,.25)],.012,WIRE,True)
# Lumpy felt cloud is a unified mesh, not a pile of intersecting spheres.
cloud_parts=[]
for dx,dy,dz,r in [(-3,0,0,1.1),(-2,0,.6,1.35),(-.5,0,.65,1.65),(1,0,.4,1.5),(2.5,0,.0,1.15),(-1,-.7,-.2,1.25),(1,-.7,-.2,1.2),(0,.8,.3,1.3)]:
    cloud_parts.append(sphere('Cloud lobe',(7+dx,2+dy,8+dz),(r,r*.67,r*.75),CLOUD))
bpy.ops.object.select_all(action='DESELECT')
for o in cloud_parts: o.select_set(True)
bpy.context.view_layer.objects.active=cloud_parts[0]; bpy.ops.object.join(); cloud=cloud_parts[0]; cloud.name='Unified sculpted felt storm cloud'
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rem=cloud.modifiers.new('Fused felt silhouette','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.095; bpy.ops.object.modifier_apply(modifier=rem.name)
sm=cloud.modifiers.new('Felt softness','SMOOTH'); sm.factor=1.1; sm.iterations=3
for p in cloud.data.polygons: p.use_smooth=True
tex=bpy.data.textures.new('Felt irregularity',type='CLOUDS'); tex.noise_scale=.19
mod=cloud.modifiers.new('Subtle felt surface','DISPLACE'); mod.texture=tex; mod.strength=.065
for i in range(95):
    x=random.uniform(3.6,10.1); y=random.uniform(1,3)
    z1=random.uniform(6.3,6.9); z2=random.uniform(1,2.9)
    rod('Fine pale rain rod',(x,y,z1),(x-.3,y-.08,z2),random.uniform(.006,.011),RAIN,6)
# Almost invisible display thread, explicitly requested by the brief.
rod('Cloud hanging filament',(7,2,9.5),(7,2,13),.0035,WHITE,6)

# Smooth street-following routes, with true arc-length animation data.
def rounded(points,rad=.3):
    out=[Vector(points[0])]
    for i in range(1,len(points)-1):
        a,b,c=map(Vector,points[i-1:i+2]); u=(a-b).normalized(); v=(c-b).normalized(); rr=min(rad,(a-b).length*.25,(c-b).length*.25)
        q=b+u*rr; r=b+v*rr; out.append(q)
        for j in range(1,9):
            t=j/8; out.append((1-t)**2*q+2*(1-t)*t*b+t*t*r)
    out.append(Vector(points[-1])); return [tuple(v) for v in out]
paths=[
 [(-12,-3.5,.37),(-9.9,-3.5,.37),(-9.9,.48,.27),(-7.98,.48,.27),(-7.98,7,.27),(12,7,.27),(12,10,.27),(13.1,10,.35)],
 [(-12,-4.9,.37),(-9.4,-4.9,.37),(-9.4,.0,.27),(2,.0,.27),(2,7,.27),(10.9,7,.27)],
 [(-12,-6.3,.37),(-8,-6.3,.27),(-8,-7,.27),(12,-7,.27),(12,-2.8,.27),(18,-2.8,.34)]]
active=COL['routes']; route_objs=[]; route_trucks=[]
for i,(pts,m) in enumerate(zip(paths,[ORANGE,BLUE,GREEN])):
    pts=rounded(pts,.55); o=curve('Route %d | drawn by bevel_factor_end'%i,pts,.072,m); route_objs.append(o)
    t=truck('Moving route truck %d'%i,pts[0],0); route_trucks.append(t)
# Pins land on actual selected houses, with a thin coloured tether from the street.
pin_specs=[(0,-6.15,10.05,.43),(0,4.55,10.05,.69),(0,14.35,10.05,.96),
 (1,-3.35,3.65,.47),(1,4.55,3.65,.74),(1,10,3.65,.97),
 (2,-3.35,-10.1,.38),(2,7.35,-10.1,.66),(2,17.2,-3.65,.96)]
pins=[]
for i,x,y,f in pin_specs:
    m=[ORANGE,BLUE,GREEN][i]; before=set(active.objects); pin=group_new('Dropping pin route %d'%i)
    rod('Coloured map pin stem',(x,y,1.99),(x,y,3.05),.026,m)
    sphere('Coloured spherical pin head',(x,y,3.12),(.18,.18,.18),m)
    parent_new(pin,before); pins.append((pin,i,f))
    sy=7 if i==0 else 0 if i==1 and x<0 else 7 if i==1 else -7 if y<-7 else -2.8
    curve('House tether '+pin.name,[(x,sy,.3),(x,y-.5,.45),(x,y,2.0)],.045,m,True)
# Persist route and pin data in the blend for a separate deterministic render script.
scene['route_paths']=json.dumps([[(p.co.x,p.co.y,p.co.z) for p in o.data.splines[0].points] for o in route_objs])
scene['pin_specs']=json.dumps([(p.name,i,f) for p,i,f in pins])
scene['house_count']=len(houses); scene['seed']=SEED

# Three separate, physically modelled problem plinths on the same seamless table.
active=COL['problems']
for x in [73.8,80,86.2]: box('Square white problem plinth',(x,0,.4),(5.25,5.25,.8),WHITE,.035)
rod('Vignette broken stump',(72.4,.15,.8),(72.4,.15,1.5),.12)
rod('Vignette snapped pole',(72.4,.15,1.4),(75,-.7,3.35),.1)
rod('Vignette fallen crossarm',(74.8,-1.3,3.35),(75.25,.1,3.35),.085)
for j in range(3): curve('Vignette loose wire',[(75,-1+j*.5,3.35),(74,-1.6+j*.3,1.0),(72.8,-1.9+j*.2,.82),(72,-1+j*.3,.82)],.019,WIRE,True)
# An upright house facade as a deliberate cut section, meter and orange horseshoe.
box('Meter house wall',(80,.35,2.2),(2.5,.21,2.8),WHITE,.016)
roof('Meter house cap',80,.35,3.6,2.5,.3,.85)
for i in range(12): box('Card siding seam',(80,.225,.94+i*.23),(2.45,.026,.018),EDGE,.002)
box('White meter enclosure',(79.7,.055,2.1),(.65,.22,.8),EDGE,.035)
rod('Meter conduit',(79.7,.08,.81),(79.7,.08,1.7),.037)
rod('White round meter face',(79.7,-.072,2.15),(79.7,-.12,2.15),.2,WHITE,32)
# Open U: back arch and two legs, oriented in the image plane.
pts=[]
for j in range(25):
    a=math.pi*j/24
    pts.append((80.45+.26*math.cos(a),-.16,1.94-.26*math.sin(a)))
magnet=curve('Orange horseshoe magnet',pts,.095,ORANGE)
bpy.context.view_layer.update()
me=bpy.data.meshes.new_from_object(magnet.evaluated_get(bpy.context.evaluated_depsgraph_get()))
bpy.data.objects.remove(magnet,do_unlink=True)
magnet=bpy.data.objects.new('Orange horseshoe magnet',me); active.objects.link(magnet)
for xx in [80.19,80.71]:
    box('Orange magnet arm',(xx,-.16,2.06),(.19,.19,.26),ORANGE,.025)
    box('Magnet white pole tip',(xx,-.16,2.22),(.19,.19,.095),EDGE,.01)
# Small solar roof, real panel cells, polished brass sun on a fine brass rod.
box('Solar house',(86.2,0,1.25),(2.9,2.65,.9),WHITE,.02)
roof('Solar roof',86.2,0,1.7,2.9,2.65,.95)
a=math.atan2(.95,1.45)
# Camera-facing slope is on the negative x side; turn panel group to face viewer via y slope.
before=set(active.objects); sol=group_new('Solar panel assembly')
box('Panel backing',(0,0,0),(1.48,2.45,.055),EDGE,.01)
for ix in range(4):
    for iy in range(8): box('Dark blue photovoltaic cell',(-.53+ix*.354,-1.065+iy*.304,.037),(.335,.287,.018),SOLAR,.003)
parent_new(sol,before)
# Panel plane follows the near roof plane, ridge along x, dedicated folded roof below.
# Rotate the entire roof/house around Z so the panel-bearing slope faces the camera.
sol.location=(85.46,-.01,2.25); sol.rotation_euler=(0,-a,0)
rod('Fine brass sun rod',(87.4,.9,.8),(87.4,.9,4.5),.026,BRASS)
sphere('Polished brass sun',(87.4,.9,4.6),(.34,.34,.34),BRASS)

for obj in COL['storm'].objects:
    if obj.name.startswith(('Broken pole','Snapped concrete','Fallen crossarm','Loose fallen')): obj.location.x-=1.2

# Broad rural strip-village board. Scale whole geometry consistently, including routes.
for cname in ['village','depot','storm','parked','dispatch','routes']:
    for obj in COL[cname].objects:
        if obj.parent is None:
            obj.location.y *= .72
            obj.scale.y *= .72
route_data=json.loads(scene['route_paths'])
for pts in route_data:
    for point in pts: point[1] *= .72
scene['route_paths']=json.dumps(route_data)
# Five photography cameras. Orthographic lenses preserve crafted-model precision.
active=COL['cameras']
def camera(name,loc,target,scale,shift=(0,0),fstop=11):
    data=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,data); active.objects.link(o)
    o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'; data.ortho_scale=scale; data.shift_x,data.shift_y=shift
    data.lens=50; data.dof.use_dof=True; data.dof.focus_distance=(Vector(target)-o.location).length; data.dof.aperture_fstop=fstop
    return o
camera('storm',(2,-30,11),(4,0,2.5),24,(-.18,.10),18)
camera('where',(-5,-21,13),(-15,-2.9,.8),19.8,(0,.12),13)
camera('problems',(80,-24,13),(80,0,2),21.3,(0,-.025),16)
camera('map',(3,-35,57),(0,0,0),59,(0,.105),35)
camera('dawn',(24,-43,22),(0,0,0),65,(0,.13),22)
# Invisible area emitters only, no light-fixture meshes.
def area(name,loc,target,power,size,color,shape='DISK'):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power*.55; d.shape=shape; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); active.objects.link(o); o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
for beat in ['storm','where','problems','map','dawn']:
    active=COL['light_'+beat]
    if beat=='storm':
        area('Overcast cool softbox',(-9,-6,24),(2,0,0),21000,20,(.91,.95,1))
        area('Cloud-side white bounce',(18,-4,14),(3,0,0),4500,12,(1,1,1))
    elif beat=='problems':
        area('Plinth large warm key',(88,-7,14),(80,0,0),4200,7,(1,.91,.79))
        area('Plinth white fill',(72,-3,10),(80,0,0),1700,8,(.91,.95,1))
    elif beat=='where':
        area('Depot low warm key',(-6,-1,7),(-15,-4,0),6800,5,(1,.83,.63))
        area('Depot soft white fill',(-20,-13,13),(-15,-4,0),4200,9,(.95,.97,1))
    else:
        area('Morning low raking key',(27,7,11),(0,0,0),23000 if beat=='map' else 25000,5,(1,.81,.57) if beat=='map' else (1,.66,.36))
        area('Neutral overhead card bounce',(-10,-7,24),(0,0,0),8500,23,(.94,.97,1))
# Backdrop illumination points away from the model, like a real product studio.
active=COL['stage']
area('Broad backdrop wash',(0,8,29),(0,24,16),12000,32,(1,.97,.91))
active=COL['light_problems']
area('Plinth backdrop wash',(80,8,29),(80,24,16),12000,32,(1,.97,.91))
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.81,.85,1); scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.engine='CYCLES'; scene.cycles.device='GPU'; scene.cycles.samples=256; scene.cycles.use_denoising=True
scene.cycles.adaptive_threshold=.02; scene.cycles.max_bounces=6; scene.cycles.diffuse_bounces=4; scene.cycles.glossy_bounces=3
scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'; scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False; scene.render.fps=30; scene.frame_start=1; scene.frame_end=180
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Very High Contrast'; scene.view_settings.exposure=-.5
scene.render.use_persistent_data=True
# Default blend opens on the completed map beat.
for n,c in COL.items(): c.hide_render=n in ['storm','parked','dispatch','problems'] or n.startswith('light_') and n!='light_map'
scene.camera=bpy.data.objects['map']
scene['notes']='Daybreak synthetic Banat architectural model. No live addresses or operational data. Rebuild seed 270611.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'daybreak.blend'))
print('DAYBREAK_BUILD '+json.dumps({'houses':len(houses),'objects':len(bpy.data.objects),'seed':SEED,'blend':str(ROOT/'daybreak.blend')}),flush=True)
