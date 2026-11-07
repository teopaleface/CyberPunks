"""Daybreak miniature props. All geometry and textures authored procedurally."""
import bpy, math, random, json, time, sys
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent
random.seed(71026)
PI=math.pi

def rgb(h):
    h=h.lstrip('#'); s=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in s)+ (1,)

def mat(name, color, rough=.55, metal=0, grain=.12, scale=110):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=rgb(color);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.7
    ramp=n.new('ShaderNodeValToRGB'); base=rgb(color)
    ramp.color_ramp.elements[0].position=.19;ramp.color_ramp.elements[0].color=tuple(c*.7 for c in base[:3])+(1,)
    ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=base
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=grain;bump.inputs['Distance'].default_value=.012
    l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m

def paint(name,color,mud=False):
    m=mat(name,color,.52,0,.16,175)
    if mud:
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
        old=p.inputs['Base Color'].links[0].from_socket
        coord=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Generated'],sep.inputs[0])
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=22;noise.inputs['Detail'].default_value=4
        l.new(coord.outputs['Generated'],noise.inputs[0]);mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.19;l.new(noise.outputs['Fac'],mul.inputs[0])
        add=n.new('ShaderNodeMath');add.operation='ADD';l.new(mul.outputs[0],add.inputs[0]);l.new(sep.outputs['Z'],add.inputs[1])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(1,1,1,1);ramp.color_ramp.elements[1].position=.39;ramp.color_ramp.elements[1].color=(0,0,0,1);l.new(add.outputs[0],ramp.inputs[0])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=rgb('#655544');l.new(ramp.outputs[0],mix.inputs[0]);l.new(old,mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])
    return m

def assign(o,m):o.data.materials.append(m);return o

def smooth(o):
    if o.type=='MESH':
        for f in o.data.polygons:f.use_smooth=True
    return o

def bevel(o,w=.025,seg=3):
    mod=o.modifiers.new('Hand finished softened edges','BEVEL');mod.width=w;mod.segments=seg
    smooth(o)
    mod=o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    return o

def box(name,loc,dim,m,b=.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
    if b:bevel(o,b)
    return o

def uv(name,loc,sc,m,seg=32,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=sc
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m);smooth(o);return o

def cyl(name,loc,rad,depth,m,axis='Z',verts=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=rad,depth=depth,location=loc);o=bpy.context.object;o.name=name
    if axis=='X':o.rotation_euler[1]=PI/2
    if axis=='Y':o.rotation_euler[0]=PI/2
    assign(o,m);smooth(o);bevel(o,min(.015,rad*.12),2);return o

def rod(name,a,b,r,m,verts=16):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,verts=verts);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def torus(name,loc,major,minor,m,axis='Z',segs=64):
    bpy.ops.mesh.primitive_torus_add(major_segments=segs,minor_segments=12,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object;o.name=name
    if axis=='Y':o.rotation_euler[0]=PI/2
    if axis=='X':o.rotation_euler[1]=PI/2
    assign(o,m);smooth(o);return o

def curve(name,pts,r,m):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=r;d.bevel_resolution=3
    s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for b,p in zip(s.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);assign(o,m);return o

def mesh(name,verts,faces,m,b=0):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);assign(o,m)
    if b:bevel(o,b)
    return o

def polyxz(name,pts,y0,y1,m,b=.02):
    n=len(pts);v=[(x,y,z) for y in (y0,y1) for x,z in pts]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,m,b)

def screw(loc,axis='Y',r=.035):
    cyl('Recessed screw head',loc,r,.012,STEEL,axis,20)
    if axis=='Y':box('Screw slot',(loc[0],loc[1]-.008,loc[2]),(r*1.3,.004,.007),DARK,.001)
    else:box('Screw slot',(loc[0],loc[1],loc[2]+.008),(r*1.3,.007,.004),DARK,.001)

def init():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):bpy.data.materials.remove(m)
    global WHITE,ORANGE,BLACK,DARK,STEEL,RUBBER,GLASS,AMBER,RED,MUD
    WHITE=paint('Warm white model enamel with lower-panel road grime','#E5E3D9',True)
    ORANGE=mat('PPC orange painted enamel','#FA4616',.48,0,.12)
    BLACK=mat('Painted charcoal steel','#24282A',.65,.35,.18)
    DARK=mat('Dark recesses','#101A1E',.65,0,.08)
    STEEL=mat('Brushed and oxidised steel','#A5AAA7',.37,.8,.16,210)
    RUBBER=mat('Dusty vulcanised rubber','#252723',.87,0,.29)
    GLASS=mat('Dark blue-grey laminated glazing','#22383F',.2,.25,.025)
    AMBER=mat('Amber indicator lenses','#E9A132',.26,0,.08)
    RED=mat('Red rear lenses','#8D2117',.3,0,.08)
    MUD=mat('Dried ochre road dust','#7B6850',.95,0,.36,140)

def wheel(x,y):
    torus('Rounded tire shoulder',(x,y,.59),.432,.145,RUBBER,'Y')
    cyl('Tire sidewall',(x,y,.59),.50,.24,RUBBER,'Y')
    outer=y+(.15 if y>0 else -.15)
    torus('Sidewall molded ring',(x,outer,.59),.405,.009,BLACK,'Y')
    cyl('Pressed steel rim',(x,outer,.59),.30,.045,STEEL,'Y')
    torus('Rim flange',(x,outer+(.027 if y>0 else -.027),.59),.27,.025,STEEL,'Y')
    cyl('Hub',(x,outer+(.03 if y>0 else -.03),.59),.12,.09,BLACK,'Y')
    for i in range(8):
        a=i*2*PI/8;xx=x+.205*math.sin(a);zz=.59+.205*math.cos(a)
        cyl('Rim ventilation', (xx,outer+(.028 if y>0 else -.028),zz),.040,.009,DARK,'Y',16)
        a+=.2;xx=x+.145*math.sin(a);zz=.59+.145*math.cos(a)
        cyl('Wheel nut',(xx,outer+(.055 if y>0 else -.055),zz),.021,.025,STEEL,'Y',6)
    for i in range(44):
        a=i*2*PI/44
        for offset in [-.078,.078]:
            o=box('Individual tread block',(x+.556*math.sin(a),y+offset,.59+.556*math.cos(a)),(.064,.105,.026),RUBBER,.008);o.rotation_euler[1]=a;o.rotation_euler[2]=.15 if offset<0 else -.15

def truck():
    # Front is -X. Side -Y faces the hero camera.
    box('Ladder chassis',(0,0,.65),(5.35,1.45,.23),BLACK,.045)
    for y in [-.57,.57]:box('Chassis rail',(.35,y,.58),(4.7,.13,.21),BLACK)
    for x in [-1.86,1.73]:
        rod('Axle',(x,-1.1,.57),(x,1.1,.57),.075,BLACK)
        for y in [-1.01,1.01]:wheel(x,y)
    # Cab has an inclined windscreen and rounded roof, with wheel arch cutouts.
    cab=polyxz('Cab pressed metal shell',[(-2.87,.80),(-2.87,1.72),(-2.56,2.46),(-2.27,2.61),(-.85,2.61),(-.72,2.44),(-.72,.80)],-.91,.91,WHITE,.07)
    for y in [-1.04,1.04]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.64,depth=.55,location=(-1.86,y,.60),rotation=(PI/2,0,0));cut=bpy.context.object
        bpy.context.view_layer.objects.active=cab;mod=cab.modifiers.new('Real wheel opening','BOOLEAN');mod.object=cut;mod.operation='DIFFERENCE';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    # Glazing, rubber surrounds and door seams are separate physical parts.
    for s in [-1,1]:
        y=s*.922
        polyxz('Window rubber gasket',[(-2.48,2.40),(-2.22,2.49),(-.96,2.49),(-.88,2.30),(-.88,1.71),(-2.69,1.71)],y-.015,y+.015,BLACK,.025)
        polyxz('Cab side glazing',[(-2.43,2.36),(-2.20,2.43),(-1.04,2.43),(-.98,2.28),(-.98,1.80),(-2.57,1.80)],y-.025,y+.025,GLASS,.026)
        box('Window divider',(-1.57,y+s*.029,2.11),(.042,.029,.66),BLACK,.008)
        curve('Door shut line',[(-.88,y+s*.014,2.42),(-.85,y+s*.014,1.67),(-.88,y+s*.014,.89),(-1.16,y+s*.014,.86)],.008,BLACK)
        box('Orange waist stripe',(-1.75,y+s*.029,1.53),(2.02,.014,.105),ORANGE,.008)
        box('Door handle',(-1.09,y+s*.05,1.62),(.22,.035,.046),BLACK,.016)
        rod('Mirror support',(-2.58,y,1.9),(-2.57,y+s*.32,2.0),.022,BLACK)
        box('Mirror housing',(-2.57,y+s*.36,2.10),(.16,.11,.31),BLACK,.04)
        box('Step below cab',(-1.11,s*.91,.72),(.62,.25,.08),STEEL,.012)
        for i in range(8):box('Antislip step rib',(-1.35+i*.065,s*.92,.765),(.02,.20,.012),BLACK,.003)
    # Sloped front glass follows front cab plane.
    verts=[(-2.872,-.77,1.83),(-2.872,.77,1.83),(-2.595,.74,2.40),(-2.595,-.74,2.40)]
    mesh('Windscreen rubber',verts,[(0,1,2,3)],BLACK)
    verts=[(-2.878,-.71,1.88),(-2.878,.71,1.88),(-2.616,.69,2.36),(-2.616,-.69,2.36)]
    mesh('Single blank windscreen',verts,[(0,1,2,3)],GLASS)
    for y in [-.44,.36]:rod('Wiper',(-2.89,y-.18,1.88),(-2.75,y+.12,2.08),.014,BLACK)
    box('Front bumper',(-2.91,0,.94),(.20,1.93,.23),BLACK,.055)
    box('Blank front grille',(-2.894,0,1.27),(.03,.82,.30),DARK,.035)
    for i in range(5):box('Grille slat',(-2.918,0,1.16+i*.052),(.014,.76,.018),STEEL,.004)
    for y in [-.66,.66]:
        box('Headlamp bezel',(-2.90,y,1.31),(.03,.40,.23),STEEL,.04)
        box('Headlamp lens',(-2.926,y,1.32),(.03,.32,.17),mat('Frosted headlight','#E9E4C5',.22,.25,.08),.035)
        box('Indicator',(-2.92,y,1.51),(.03,.28,.075),AMBER,.014)
    # Cabinet service body, hinges, latches, deck and boom.
    box('Aluminium working deck',(1.02,0,1.10),(3.38,1.91,.18),STEEL,.035)
    for y in [-.78,.78]:
        box('Service locker bank',(1.0,y,1.43),(3.45,.46,.66),WHITE,.045)
        box('Continuous thin orange side stripe',(1,y+(-.245 if y<0 else .245),1.60),(3.37,.012,.098),ORANGE,.004)
        for x in [-.10,.83,1.84,2.52]:
            box('Locker door seam',(x,y+(-.239 if y<0 else .239),1.38),(.012,.007,.49),BLACK,.002)
        for x in [-.33,.38,1.35,2.21]:
            box('Recessed cabinet latch',(x,y+(-.252 if y<0 else .252),1.36),(.14,.018,.078),BLACK,.008)
            for z in [1.22,1.49]:box('Locker hinge',(x-.30,y+(-.252 if y<0 else .252),z),(.05,.027,.095),STEEL,.006)
        box('Rear mud flap',(2.35,y,.45),(.10,.49,.44),RUBBER,.015)
        box('Folded outrigger housing',(.60,y,1.0),(.33,.53,.24),STEEL,.025)
        box('Outrigger foot',(.60,y,.84),(.39,.35,.07),BLACK,.012)
    box('Rear step bumper',(2.85,0,.97),(.25,2.02,.14),STEEL,.025)
    for y in [-.78,.78]:box('Tail lamp',(2.795,y,1.35),(.04,.21,.17),RED,.02)
    cyl('Slew pedestal',(.90,0,1.48),.38,.60,WHITE)
    cyl('Slew bearing',(.90,0,1.80),.43,.12,BLACK)
    box('Boom knuckle',(.99,0,1.97),(.65,.43,.34),WHITE,.06)
    # Folded Z boom, pivot caps, polished hydraulic ram, black hydraulic hoses.
    a=(1.15,0,2.02);b=(-.12,0,2.79);c=(2.09,0,2.86)
    def beam(name,a,b,width,height,m):
        a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,height,(b-a).length),m,.035);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
    beam('Folded lower boom',a,b,.29,.36,WHITE)
    beam('Folded upper boom',b,c,.23,.28,WHITE)
    for x,z in [(1.15,2.02),(-.12,2.79),(2.09,2.86)]:
        cyl('Boom pin',(x,0,z),.13,.47,STEEL,'Y')
        for y in [-.25,.25]:cyl('Orange pivot cap',(x,y,z),.087,.02,ORANGE,'Y')
    rod('Hydraulic cylinder',(1.39,-.26,1.95),(.13,-.26,2.55),.064,STEEL)
    rod('Hydraulic piston',(.13,-.26,2.55),(-.07,-.26,2.72),.034,STEEL)
    curve('Hydraulic hoses',[(1.25,-.25,1.7),(.43,-.25,2.23),(-.23,-.25,2.8),(.13,-.21,3.0),(1.95,-.21,3.0)],.026,RUBBER)
    box('Bucket outer shell',(2.28,0,2.63),(.79,.82,.64),WHITE,.09)
    box('Bucket inner cavity',(2.28,0,2.96),(.60,.64,.015),DARK,.055)
    for y in [-.40,.40]:box('Bucket rim',(2.28,y,2.98),(.80,.08,.09),WHITE,.035)
    for x in [1.91,2.65]:box('Bucket rim',(x,0,2.98),(.08,.77,.09),WHITE,.035)
    for y in [-.56,.56]:
        cyl('Amber work beacon',(-.98,y,2.70),.105,.16,AMBER)
        cyl('Beacon mount',(-.98,y,2.62),.12,.045,BLACK)
    # Small paint chips and dust, restricted to metal lower edges.
    for i in range(120):
        x=random.uniform(-.65,2.7); y=random.choice([-1.018,1.018]);z=random.uniform(1.13,1.25)
        o=box('Fine dried mud fleck',(x,y,z),(random.uniform(.008,.035),.004,random.uniform(.005,.018)),MUD,.002)
    for i in range(24):
        x=random.uniform(-.4,2.5);y=random.choice([-.998,.998]);z=random.uniform(1.66,1.73)
        box('Enamel edge chip',(x,y,z),(.025,.005,.007),STEEL,.002)

def magnet():
    # U in XZ plane, open at the bottom. Extruded rounded horseshoe.
    r=.59;th=.21;z=.06;y=-.373
    pts=[]
    # continuous U path, left tip -> arc -> right tip
    pts.append((-.59,y,z-.43))
    for i in range(33):
        a=PI-i*PI/32;pts.append((r*math.cos(a),y,z+.05+r*math.sin(a)))
    pts.append((.59,y,z-.43))
    # Sweep a rounded square cross-section for forged magnet.
    verts=[];N=12
    for i,p in enumerate(pts):
        t=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])).normalized();n=Vector((-t.z,0,t.x))
        for j in range(N):
            a=2*PI*j/N;off=n*(math.cos(a)*th/2)+Vector((0,math.sin(a)*.105,0));verts.append(Vector(p)+off)
    faces=[]
    for i in range(len(pts)-1):
        for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
    faces.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
    red=mat('Worn vermilion magnet enamel','#BD3023',.43,.25,.13,210)
    o=mesh('Solid forged horseshoe magnet',verts,faces,red);smooth(o)
    for x in [-.59,.59]:
        box('Orange magnet foot',(x,y,z-.39),(.224,.222,.20),ORANGE,.035)
        box('Exposed magnet pole face',(x,y,z-.502),(.207,.205,.025),STEEL,.015)
    for i in range(20):
        a=random.uniform(.15,PI-.15);x=r*math.cos(a);zz=z+.05+r*math.sin(a)
        box('Minute magnet enamel wear',(x,y-.105,zz),(.022,.0015,.003),STEEL,.001)

def meter():
    grey=paint('Meter warm-grey textured ABS','#CACCC4')
    edge=mat('Weathered gasket','#62675F',.83,0,.2)
    body=box('Moulded electricity meter enclosure',(0,0,0),(1.95,.51,2.65),grey,.13)
    box('Rear mounting plate',(0,.20,0),(2.06,.16,2.84),mat('Powder coated back plate','#919B94',.65,.1,.17),.06)
    for z in [-1.38,1.38]:
        box('Mounting lug',(0,.22,z),(.43,.13,.22),grey,.055)
        cyl('Mounting hole',(0,.141,z),.054,.015,DARK,'Y',24)
    box('Case perimeter gasket',(0,-.26,0),(1.79,.018,2.46),edge,.11)
    box('Front case',(0,-.279,.02),(1.76,.055,2.40),grey,.10)
    box('Display recessed black surround',(0,-.326,.71),(1.31,.045,.51),BLACK,.052)
    box('Blank dark LCD',(0,-.355,.72),(1.16,.025,.36),mat('Blank smoked LCD glass','#27332E',.20,.05,.02),.022)
    # Fine inset glass catches softbox, without letters or digits.
    box('Display glass top edge',(0,-.371,.88),(1.10,.006,.009),STEEL,.003)
    box('Terminal cover', (0,-.332,-.91),(1.61,.085,.48),grey,.055)
    box('Terminal cover separation',(0,-.379,-.65),(1.54,.008,.012),edge,.003)
    for x in [-.68,.68]:
        for z in [-1.08,1.08]:screw((x,-.371,z))
    for x in [-.54,-.27,0,.27,.54]:
        cyl('Cable entry gland',(x,.01,-1.36),.09,.13,edge,'Z',24)
        cyl('Cable entry darkness',(x,.01,-1.432),.055,.008,DARK)
    # One cable pair curls backwards, away from the magnet silhouette.
    curve('Meter feed cable',[(-.54,.01,-1.42),(-.56,.01,-1.67),(-.39,.13,-1.79),(-.20,.26,-1.62)],.045,RUBBER)
    curve('Meter feed cable',[(.54,.01,-1.42),(.56,.01,-1.62),(.48,.19,-1.77),(.33,.30,-1.64)],.045,RUBBER)
    # Blank optical sensor and shallow ventilation recesses.
    cyl('Optical port',(.60,-.355,.30),.065,.03,DARK,'Y')
    for x in [-.81,.81]:
        for z in [-.35,-.21,-.07,.07]:box('Side vents',(x,-.31,z),(.04,.018,.055),edge,.008)
    magnet()
    # Scuff marks at the lower cover, physical mould seam around the housing.
    for i in range(34):
        x=random.uniform(-.70,.70);z=random.uniform(-1.12,-.78)
        box('Fine accumulated dust',(x,-.379,z),(random.uniform(.008,.025),.002,.004),MUD,.001)

BUILDERS={'truck':truck,'meter':meter}

sys.path.insert(0,str(ROOT))
from more_objects import extend
extend(globals())

def setup(name):
    scene=bpy.context.scene
    props=list(scene.objects)
    # Apply modifier stacks once, join by material to make animation rendering inexpensive.
    bpy.ops.object.select_all(action='DESELECT')
    for o in props:
        if o.type=='MESH':
            bpy.context.view_layer.objects.active=o
            for mod in list(o.modifiers):
                try:bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception:pass
    groups={}
    for o in props:
        if o.type=='MESH':groups.setdefault(o.active_material.name if o.active_material else '',[]).append(o)
    for objects in groups.values():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
    # Geometry centred at its bounding-box centre, with no ground or catcher.
    props=list(scene.objects);bpy.context.view_layer.update()
    bounds=[o.matrix_world@Vector(v) for o in props for v in o.bound_box]
    lo=Vector(tuple(min(v[i] for v in bounds) for i in range(3)));hi=Vector(tuple(max(v[i] for v in bounds) for i in range(3)));center=(hi+lo)/2
    for o in props:o.location-=center
    root=bpy.data.objects.new('PROP_PIVOT',None);scene.collection.objects.link(root)
    for o in props:o.parent=root
    bpy.context.view_layer.update()
    radius=max((o.matrix_world@Vector(v)).length for o in props for v in o.bound_box)
    # Macro product camera, generous lens distance to keep silhouette undistorted.
    direction=Vector((-6,-9,5.2)).normalized() if name=='truck' else Vector((4,-10,4.4)).normalized()
    if name=='solar':direction=Vector((3.5,-5,9)).normalized()
    if name=='meter':direction=Vector((3.3,-12,3.7)).normalized()
    bpy.ops.object.camera_add(location=direction*radius*6.7);cam=bpy.context.object;cam.name='Macro studio camera';cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    cam.data.type='PERSP';cam.data.lens=70;cam.data.sensor_width=36;cam.data.clip_start=.0001;cam.data.clip_end=100
    # Tight hero framing from projected bounding box.
    bpy.context.view_layer.update()
    inv=cam.matrix_world.inverted()
    projected=[];deps=bpy.context.evaluated_depsgraph_get()
    for o in props:
        ev=o.evaluated_get(deps);me=ev.to_mesh()
        if me:projected.extend(inv@(o.matrix_world@v.co) for v in me.vertices)
        ev.to_mesh_clear()
    # Fit the real silhouette in a perspective camera with 12% minimum padding.
    old_distance=cam.location.length;tan_limit=(cam.data.sensor_width/(2*cam.data.lens))*.76
    hero_distance=max(old_distance+v.z+max(abs(v.x),abs(v.y))/tan_limit for v in projected)
    spin_distance=radius*math.sqrt(1+1/tan_limit**2)
    physical_scale=1/87
    root.scale=(physical_scale,)*3
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type=='BUMP':node.inputs['Distance'].default_value*=physical_scale
                if node.type=='BSDF_PRINCIPLED':node.inputs['Subsurface Scale'].default_value*=physical_scale
    cam.location=direction*hero_distance*physical_scale
    focus=Vector((-1,-.65,-.1)) if name=='truck' else Vector((0,-.37,.25)) if name=='meter' else Vector((0,0,0))
    cam.data.dof.use_dof=True;cam.data.dof.focus_distance=cam.location.length-direction.dot(focus)*physical_scale;cam.data.dof.aperture_fstop=32 if name=='truck' else 64;cam.data.dof.aperture_blades=9
    def area(n,vec,power,col,size):
        bpy.ops.object.light_add(type='AREA',location=Vector(vec)*radius);o=bpy.context.object;o.name=n;o.data.energy=power*radius*radius;o.data.color=col;o.data.shape='DISK';o.data.size=size*radius;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    area('Large warm upper left softbox',(-3,-4,6),650,(1,.82,.64),4)
    area('Cool narrow back-right rim',(3,2.8,4),850,(.55,.73,1),3)
    area('Gentle frontal fill',(2,-4,1.0),160,(.76,.86,1),4)
    # Preserve illumination while moving the studio to a real 1:87 model scale.
    for light in [o for o in scene.objects if o.type=='LIGHT']:
        light.location*=physical_scale;light.data.size*=physical_scale;light.data.energy*=physical_scale**2
    scene.world.color=(.10,.10,.10)
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.12,.15,.19,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.23
    scene.render.engine='CYCLES';scene.cycles.device='GPU';p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
    for d in p.devices:d.use=d.type=='METAL'
    scene.cycles.samples=80;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_use_gpu=True;scene.cycles.adaptive_threshold=.035
    scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.cycles.transparent_max_bounces=6
    scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.film_transparent=True
    scene.render.fps=30;scene.render.fps_base=1
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.25
    scene.render.threads_mode='FIXED';scene.render.threads=6
    scene['object_name']=name;scene['radius']=radius*physical_scale;scene['hero_camera_distance']=hero_distance*physical_scale;scene['spin_camera_distance']=spin_distance*physical_scale;scene['authored_units']='Physical metres, 1:87 model scale';scene['camera_projection']='Perspective 70 mm macro'
    bpy.context.view_layer.update()
    return scene

def build(name,render=True):
    t=time.perf_counter();init()
    sys.modules['more_objects'].__dict__.update(globals())
    BUILDERS[name]();scene=setup(name);out=ROOT/name;out.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
    built=time.perf_counter()-t
    if render:
        scene.render.filepath=str(out/'hero.png');t=time.perf_counter();bpy.ops.render.render(write_still=True);elapsed=time.perf_counter()-t
        timings=json.loads((ROOT/'timings.json').read_text()) if (ROOT/'timings.json').exists() else {}
        timings.setdefault(name,{}).update(build_seconds=round(built,3),hero_seconds=round(elapsed,3),hero_samples=scene.cycles.samples)
        (ROOT/'timings.json').write_text(json.dumps(timings,indent=2))
        print('OBJECTS_HERO_DONE',name,elapsed,flush=True)

if __name__=='__main__':
    names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['truck','meter']
    for name in names:build(name)
