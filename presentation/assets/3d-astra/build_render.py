"""Procedural, original Blender geometry for Tura de maine. No external assets.
Run using Blender 5.2.1; see README.md. All output remains beside this script.
"""
import bpy, math, sys, argparse, json, time
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

OUT = Path(__file__).resolve().parent
NAMES = ['meter', 'transformer', 'solar', 'storm', 'helmet']
P = argparse.ArgumentParser()
P.add_argument('--objects', nargs='+', choices=NAMES, default=NAMES)
P.add_argument('--mode', choices=['heroes','spin','all'], default='all')
P.add_argument('--samples', type=int, default=32)
P.add_argument('--hero-samples', type=int, default=96)
P.add_argument('--engine', choices=['CYCLES','BLENDER_EEVEE'], default='CYCLES')
ARGS = P.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def rgba(h):
    h=h.lstrip('#'); a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in a)+(1,)

def mat(name, color, metal=0, rough=.25, coat=.25, emission=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=rgba(color)
    s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=rough
    s.inputs['Coat Weight'].default_value=coat; s.inputs['Coat Roughness'].default_value=.19
    s.inputs['Emission Color'].default_value=rgba(color); s.inputs['Emission Strength'].default_value=emission
    return m

def smooth(o):
    if o.type=='MESH':
        for f in o.data.polygons: f.use_smooth=True
    return o

def bevel(o, width=.03, segments=4):
    b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=width; b.segments=segments
    n=o.modifiers.new('Stable surface normals','WEIGHTED_NORMAL'); n.keep_sharp=True; n.weight=50
    return o

def assign(o,m):
    o.data.materials.append(m); return o

def box(name, loc, dims, m, r=.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name
    o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,m); smooth(o)
    if r: bevel(o,r,5)
    return o

def mesh(name, verts, faces, m, bevel_width=0, smoothing=True):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); assign(o,m)
    if smoothing: smooth(o)
    if bevel_width: bevel(o,bevel_width,5)
    return o

def sphere(name,loc,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=48,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; assign(o,m); smooth(o); return o

def cylinder(name,loc,r,depth,m,axis='Z',verts=96,edge=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    o=bpy.context.object; o.name=name
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    elif axis=='X': o.rotation_euler[1]=math.pi/2
    assign(o,m)
    if verts>8: smooth(o)
    if edge: bevel(o,edge,4)
    return o

def torus(name,loc,major,minor,m,axis='Z'):
    bpy.ops.mesh.primitive_torus_add(major_segments=96,minor_segments=16,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object; o.name=name
    if axis=='Y': o.rotation_euler[0]=math.pi/2
    assign(o,m); smooth(o); return o

def rounded_rect(name,loc,w,h,d,r,m,plane='XZ',edge=.012):
    # Independent planar corner radius and depth bevel; not a scaled cube.
    pts=[]
    for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for k in range(13):
            a=math.radians(start+90*k/12); pts.append((cx+r*math.cos(a),cz+r*math.sin(a)))
    n=len(pts); vs=[]
    for dep in [-d/2,d/2]:
        for x,z in pts: vs.append((x,dep,z) if plane=='XZ' else (x,z,dep))
    # Winding of XZ planes has opposite orientation to XY.
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    if plane=='XZ': fs=[tuple(reversed(f)) for f in fs]
    o=mesh(name,vs,fs,m,edge); o.location=loc; return o

def extruded_xz(name,points,depth,m,loc=(0,0,0),edge=.04):
    n=len(points); vs=[(x,y,z) for y in [-depth/2,depth/2] for x,z in points]
    fs=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    o=mesh(name,vs,fs,m,edge); o.location=loc; return o

def lathe(name,loc,profile,m):
    n=96; vs=[(r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z) for r,z in profile for i in range(n)]
    fs=[]
    for j in range(len(profile)-1):
        for i in range(n): fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    fs += [tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))]
    o=mesh(name,vs,fs,m); o.location=loc
    s=o.modifiers.new('Continuous porcelain curvature','SUBSURF'); s.levels=2
    return o

def tube(name,points,r,m):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=20
    cu.bevel_depth=r; cu.bevel_resolution=5
    p=cu.splines.new('BEZIER'); p.bezier_points.add(len(points)-1)
    for b,co in zip(p.bezier_points,points): b.co=co; b.handle_left_type='AUTO'; b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(o); assign(o,m); return o

def screw(name,x,y,z,r=.045):
    cylinder(name+' recessed seat',(x,y+.006,z),r*1.25,.025,M['seam'],'Y',edge=.005)
    cylinder(name+' metal cap',(x,y-.008,z),r,.022,M['steel'],'Y',edge=.008)
    for angle in [0,math.pi/2]:
        s=box(name+' cross recess',(x,y-.021,z),(r*1.25,.004,r*.18),M['seam'],r*.06); s.rotation_euler[1]=angle

def setup():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for datablocks in [bpy.data.materials,bpy.data.meshes,bpy.data.curves,bpy.data.cameras,bpy.data.lights]:
        for d in list(datablocks):
            if d.users==0: datablocks.remove(d)
    global M
    M={
      'white':mat('Warm clean white polymer','F4F6F9',rough=.235,coat=.32),
      'porcelain':mat('White glazed porcelain','F7F8FC',rough=.19,coat=.45),
      'back':mat('Rear shell pearl grey','DEE3E9',rough=.29,coat=.25),
      'ink':mat('Ink navy 0B1622','0B1622',rough=.29,coat=.12),
      'seam':mat('Inset charcoal grey','273442',metal=.25,rough=.28),
      'steel':mat('Satin aluminium','CFD6DE',metal=.7,rough=.31,coat=.16),
      'edge':mat('Polished edge metal','E5EBF1',metal=.82,rough=.2,coat=.18),
      'amber':mat('Amber enamel F2A20C','F2A20C',metal=.16,rough=.21,coat=.45),
    }
    scene=bpy.context.scene; scene.render.engine=ARGS.engine
    scene.render.film_transparent=True; scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'; scene.render.image_settings.color_depth='8'
    scene.render.image_settings.compression=25
    scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
    scene.view_settings.exposure=0; scene.view_settings.gamma=1
    scene.render.resolution_percentage=100; scene.render.fps=30
    scene.render.use_file_extension=True; scene.render.threads_mode='AUTO'
    if ARGS.engine=='CYCLES':
        scene.cycles.samples=ARGS.samples; scene.cycles.use_denoising=True
        scene.cycles.denoiser='OPENIMAGEDENOISE'; scene.cycles.use_adaptive_sampling=True
        scene.cycles.adaptive_threshold=.025; scene.cycles.adaptive_min_samples=16
        scene.cycles.max_bounces=6; scene.cycles.diffuse_bounces=3; scene.cycles.glossy_bounces=4
        scene.cycles.transparent_max_bounces=4; scene.cycles.seed=19
        prefs=bpy.context.preferences.addons['cycles'].preferences
        try:
            prefs.compute_device_type='METAL'; prefs.get_devices()
            for device in prefs.devices: device.use=device.type=='METAL'
            scene.cycles.device='GPU'
            print('RENDER_DEVICES',[(d.name,d.type,d.use) for d in prefs.devices],flush=True)
        except Exception as e: print('METAL unavailable; using CPU:',e,flush=True); scene.cycles.device='CPU'
        scene.render.use_persistent_data=True
    scene.world=bpy.data.worlds.new('Neutral studio environment'); scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(1,1,1,1); bg.inputs[1].default_value=.40
    def area(name,loc,power,size,color=(1,1,1),shape='DISK',size_y=None):
        data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape=shape; data.size=size; data.color=color
        if size_y: data.size_y=size_y
        o=bpy.data.objects.new(name,data); scene.collection.objects.link(o); o.location=loc
        o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key large softbox',(-3.8,-4.4,6.8),135,4.0,(1,.98,.96),'RECTANGLE',5.5)
    area('Right tall reflection card',(4.5,-1.5,3.2),75,2.0,(.92,.96,1),'RECTANGLE',4.5)
    area('Back rim',(-1,4.2,5.5),100,3.4,(1,1,1),'RECTANGLE',2.7)
    area('Large frontal fill',(0,-5,1),85,5,(1,1,1),'DISK')
    camera=bpy.data.cameras.new('Shared orthographic camera'); co=bpy.data.objects.new('Shared orthographic camera',camera)
    scene.collection.objects.link(co); co.location=(6,-11,4.8); co.rotation_euler=(-co.location).to_track_quat('-Z','Y').to_euler()
    camera.type='ORTHO'; camera.ortho_scale=4.8; camera.lens=60; camera.clip_end=100; scene.camera=co
    scene.render.resolution_x=scene.render.resolution_y=1024
    return scene

def meter():
    box('Rounded back enclosure',(0,.08,0),(1.94,.72,2.68),M['back'],.23)
    rounded_rect('Cover gasket',(0,-.285,0),1.86,2.56,.065,.22,M['back'],edge=.018)
    rounded_rect('Main moulded face',(0,-.355,.35),1.88,1.88,.19,.22,M['white'],edge=.045)
    rounded_rect('Separate terminal cover',(0,-.35,-.97),1.87,.72,.19,.18,M['white'],edge=.04)
    rounded_rect('Screen anodised perimeter',(0,-.467,.55),1.53,1.01,.065,.18,M['edge'],edge=.015)
    rounded_rect('Ink bezel',(0,-.503,.55),1.505,.985,.055,.16,M['ink'],edge=.013)
    m=mat('Blue screen, procedural centre glow','2364D2',metal=.02,rough=.23,coat=.15)
    nt=m.node_tree; nd=nt.nodes; li=nt.links; shader=nd.get('Principled BSDF')
    coord=nd.new('ShaderNodeTexCoord'); separate=nd.new('ShaderNodeSeparateXYZ'); li.new(coord.outputs['Generated'],separate.inputs[0])
    combine=nd.new('ShaderNodeCombineXYZ'); li.new(separate.outputs['X'],combine.inputs['X']); li.new(separate.outputs['Z'],combine.inputs['Y'])
    dist=nd.new('ShaderNodeVectorMath'); dist.operation='DISTANCE'; dist.inputs[1].default_value=(.5,.42,0); li.new(combine.outputs[0],dist.inputs[0])
    ramp=nd.new('ShaderNodeValToRGB'); ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(pos,col) in enumerate([(0,'2364D2'),(.29,'164394'),(.62,'09182C')]):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos); e.position=pos; e.color=rgba(col)
    ramp.color_ramp.interpolation='EASE'; li.new(dist.outputs['Value'],ramp.inputs[0]); li.new(ramp.outputs[0],shader.inputs['Base Color']); li.new(ramp.outputs[0],shader.inputs['Emission Color']); shader.inputs['Emission Strength'].default_value=.65; shader.inputs['Specular IOR Level'].default_value=.23
    rounded_rect('Continuous blue glass',(0,-.537,.55),1.34,.78,.028,.12,m,edge=.009)
    torus('Control rim',(.575,-.469,-.32),.105,.015,M['edge'],'Y')
    cylinder('Satin circular control',(.575,-.477,-.32),.094,.033,M['steel'],'Y',edge=.014)
    for i in [-1,1]: screw('Security screw',i*.69,-.46,-.93,.047)
    cylinder('Status indicator housing',(-.65,-.462,-.33),.032,.016,M['ink'],'Y',edge=.004)
    led=mat('Blue status light','2364D2',rough=.2,emission=.7)
    cylinder('Status indicator',(-.65,-.475,-.33),.018,.012,led,'Y',edge=.003)
    # Rear mounting channel, side vents and terminal entries remain real in side views.
    box('Rear DIN attachment',(0,.475,.07),(1.1,.13,1.82),M['ink'],.09)
    for side in [-1,1]:
        for j in range(5): box('Side ventilation recess',(side*.966,.14,-.44+j*.15),(.015,.19,.038),M['seam'],.009)
        cylinder('Cable entry',(side*.42,.03,-1.36),.13,.09,M['back'],edge=.015)
        cylinder('Cable entry dark centre',(side*.42,.03,-1.406),.082,.014,M['ink'],edge=.005)


def transformer():
    metal=mat('Transformer satin silver','CAD3DD',metal=.65,rough=.30,coat=.18)
    concrete=mat('Fine cast concrete','CDD0D2',rough=.69,coat=0)
    nt=concrete.node_tree; ns=nt.nodes; lk=nt.links; bs=ns.get('Principled BSDF')
    tc=ns.new('ShaderNodeTexCoord'); noise=ns.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=48; noise.inputs['Detail'].default_value=2
    lk.new(tc.outputs['Object'],noise.inputs['Vector']); ramp=ns.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=rgba('B8BABC'); ramp.color_ramp.elements[1].color=rgba('E1E2E4'); lk.new(noise.outputs['Fac'],ramp.inputs[0]); lk.new(ramp.outputs[0],bs.inputs['Base Color'])
    bump=ns.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.17; bump.inputs['Distance'].default_value=.013; lk.new(noise.outputs['Fac'],bump.inputs['Height']); lk.new(bump.outputs[0],bs.inputs['Normal'])
    px,py=-1.03,.30
    cylinder('Short concrete pole',(px,py,-.03),.225,2.95,concrete,edge=.025)
    for z in [.47,-.83]:
        cylinder('Pole steel strap',(px,py,z),.238,.145,M['steel'],edge=.012)
        box('Mounting saddle',(-.64,.31,z),(.82,.25,.12),M['steel'],.025)
        box('Bolt pad',(px,py-.26,z),(.27,.065,.22),M['steel'],.025)
        screw('Pole clamp bolt',px,py-.30,z,.055)
    box('Rear mounting spine',(-.72,.35,-.26),(.14,.17,1.76),M['steel'],.025)
    brace=box('Diagonal support',(-.54,.23,-.90),(.11,.15,.78),M['steel'],.025); brace.rotation_euler[1]=-.70
    cylinder('Tank barrel',(0,0,-.08),.73,1.34,metal,edge=.085)
    cylinder('Bottom rolled rim',(0,0,-.74),.75,.10,M['steel'],edge=.025)
    for i in range(24):
        a=2*math.pi*i/24
        o=rounded_rect('Radiator fin %02d'%i,(.753*math.cos(a),.753*math.sin(a),-.07),.23,1.10,.045,.105,metal,edge=.014)
        o.rotation_euler[2]=a
    cylinder('Lid seal',(0,0,.592),.775,.035,M['seam'],edge=.008)
    cylinder('Tank lid',(0,0,.66),.83,.135,M['steel'],edge=.033)
    cylinder('Raised lid crown',(0,0,.735),.75,.07,metal,edge=.032)
    for i in range(12):
        a=2*math.pi*i/12; x,y=.777*math.cos(a),.777*math.sin(a)
        cylinder('Lid washer',(x,y,.74),.038,.016,M['edge'],edge=.003)
        cylinder('Lid hex bolt',(x,y,.76),.028,.035,M['steel'],verts=6,edge=.004)
    profile=[(.085,0),(.10,.01),(.10,.09)]
    for bottom,r in [(.09,.18),(.245,.17),(.40,.155)]:
        profile += [(.10,bottom+.005),(.105,bottom+.025),(r*.94,bottom+.049),(r,bottom+.066),(r*.96,bottom+.082),(.112,bottom+.12),(.085,bottom+.15)]
    profile += [(.074,.585),(.074,.60),(.069,.61)]
    for i,x in enumerate([-.49,0,.49]):
        y=.025 if i!=1 else -.045
        cylinder('Bushing flange',(x,y,.80),.141,.065,M['edge'],edge=.012)
        lathe('Porcelain three-shed insulator',(x,y,.82),profile,M['porcelain'])
        cylinder('Terminal collar',(x,y,1.43),.084,.05,M['steel'],edge=.007)
        cylinder('Terminal nut',(x,y,1.485),.073,.065,M['steel'],verts=6,edge=.006)
        cylinder('Terminal stud',(x,y,1.55),.036,.10,M['steel'],edge=.004)
        for j in range(5): torus('Terminal screw thread',(x,y,1.522+j*.014),.036,.0035,M['edge'])
    cylinder('Drain ferrule',(.34,-.20,-.84),.075,.12,M['steel'],edge=.01)
    cylinder('Drain cap',(.34,-.20,-.91),.065,.045,M['steel'],verts=6,edge=.007)


def solar():
    roof=mat('Ink navy glazed roof tiles','162638',metal=.22,rough=.28,coat=.32)
    cells=[mat('Monocrystalline cell %d'%i,c,metal=.07,rough=.21,coat=.13) for i,c in enumerate(['142C4E','162F54','172E51','132B4A'])]
    for cell in cells: cell.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.22
    lines=mat('Fine cell conductor','61738C',metal=.25,rough=.36)
    # White section of a gabled roof. Actual shell thickness and both slopes.
    yz=[(-1.06,-.29),(.12,.70),(.93,.02),(.93,-.12),(.12,.54),(-1.06,-.45)]
    vs=[(x,y,z) for x in [-1.32,1.32] for y,z in yz]; n=len(yz)
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh('White gable roof section',vs,fs,M['white'],.045)
    angle=math.radians(40); front_origin=Vector((0,-.47,.255))
    def oriented(o,center,rx):
        o.rotation_euler[0]=rx; o.location=center; return o
    # Overlapping, curved individual tiles instead of a flat textured sheet.
    for back in [False,True]:
        length=1.56 if not back else 1.075; origin=front_origin if not back else Vector((0,.525,.36)); rx=angle if not back else -angle
        rot=Matrix.Rotation(rx,4,'X')
        for row in range(3):
            for col in range(7):
                width=2.64/7; llen=length/3+.06; x0=-1.32+col*width
                vv=[]; ff=[]
                for j in range(5):
                    t=j/4; ly=-length/2+row*length/3+t*llen
                    for k in range(13):
                        u=k/12; lx=x0+u*width
                        zz=.035+.026*math.cos(2*math.pi*u)+.018*(1-t)
                        p=rot@Vector((lx,ly,zz))+origin; vv.append(tuple(p))
                for j in range(4):
                    for k in range(12):
                        a=j*13+k; ff.append((a,a+1,a+14,a+13))
                o=mesh('Curved roof tile',vv,ff,roof); so=o.modifiers.new('Tile thickness','SOLIDIFY'); so.thickness=.023
                b=o.modifiers.new('Glazed tile lip','BEVEL'); b.width=.008; b.segments=3
    # Build panel in local XY, then tilt its full assembly to the roof.
    start=set(bpy.context.scene.objects)
    rounded_rect('Panel aluminium frame',(0,0,0),2.28,1.40,.105,.075,M['edge'],'XY',.018)
    rounded_rect('Cell perimeter gasket',(0,0,.06),2.15,1.27,.025,.035,M['ink'],'XY',.007)
    for row in range(3):
        for col in range(4):
            x=(col-1.5)*.524; y=(row-1)*.407
            rounded_rect('PV cell %d %d'%(row,col),(x,y,.079),.508,.391,.016,.038,cells[(row+col)%4],'XY',.005)
            for stripe in range(1,13):
                yy=y-.181+stripe*.028
                box('Etched cell conductor',(x,yy,.089),(.46,.0009,.0007),lines,0)
    for x in [-.78,.78]:
        box('Underside support rail',(x,0,-.09),(.08,1.25,.07),M['steel'],.01)
        # Bottom attachment hook with rounded bends.
        points=[(-.75,-.09),(-.66,-.09),(-.63,.02),(-.57,.03),(-.57,.075),(-.69,.075),(-.72,-.035),(-.75,-.035)]
        # Profile coordinates are panel-local y,z; thickness in x.
        verts=[(xx,yy,zz) for xx in [x-.055,x+.055] for yy,zz in points]; nn=len(points)
        faces=[tuple(range(nn-1,-1,-1)),tuple(range(nn,nn*2))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
        mesh('Curved panel clamp',verts,faces,M['steel'],.012)
        cylinder('Clamp bolt',(x,-.61,.099),.032,.023,M['edge'],edge=.006)
    box('Rear junction enclosure',(0,.2,-.12),(.35,.22,.09),M['ink'],.03)
    panel_center=Vector((0,-.30,.515)); rot=Matrix.Rotation(angle,4,'X')
    for o in set(bpy.context.scene.objects)-start:
        o.location=rot@o.location+panel_center; o.rotation_euler=(rot.to_3x3()@o.rotation_euler.to_matrix()).to_euler()
    sun=mat('Glossy amber sun','F2A20C',metal=.06,rough=.20,coat=.5,emission=.13)
    sphere('Amber sun sphere',(.90,.60,1.22),(.43,.43,.43),sun)


def storm():
    cloud=mat('Cloud pearl with plum underside','F5F4FA',metal=.025,rough=.30,coat=.20)
    nt=cloud.node_tree; nd=nt.nodes; lk=nt.links; bs=nd.get('Principled BSDF')
    tc=nd.new('ShaderNodeTexCoord'); sep=nd.new('ShaderNodeSeparateXYZ'); lk.new(tc.outputs['Generated'],sep.inputs[0]); ramp=nd.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(p,col) in enumerate([(0,'86317F'),(.18,'A23C9E'),(.43,'D8C5DC'),(.66,'EEF0F6'),(1,'F8F9FC')]):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(p); e.position=p; e.color=rgba(col)
    ramp.color_ramp.interpolation='EASE'; lk.new(sep.outputs['Z'],ramp.inputs[0]); lk.new(ramp.outputs[0],bs.inputs['Base Color'])
    parts=[]
    for loc,scale in [((-.64,0,.15),(.64,.52,.56)),((-.03,0,.52),(.72,.53,.76)),((.64,0,.17),(.65,.51,.59)),((-.02,0,-.05),(.97,.52,.36))]:
        parts.append(sphere('Cloud volume',loc,scale,cloud))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); o=bpy.context.object; o.name='Continuous rounded cloud'
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    rem=o.modifiers.new('Union cloud lobes','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.022; rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=o.modifiers.new('Soft lobe junctions','SMOOTH'); sm.factor=.85; sm.iterations=55; bpy.ops.object.modifier_apply(modifier=sm.name)
    sub=o.modifiers.new('Smooth cloud silhouette','SUBSURF'); sub.levels=1
    pts=[(-.12,.15),(.40,.15),(.06,-.40),(.43,-.40),(-.40,-1.43),(-.17,-.70),(-.57,-.70)]
    # Round the silhouette itself so the lower tip cannot clamp the bevel to zero.
    rounded=[]
    for i,p in enumerate(pts):
        p=Vector(p); before=Vector(pts[i-1]); after=Vector(pts[(i+1)%len(pts)])
        distance=min(.105,(before-p).length*.24,(after-p).length*.24)
        a=p+(before-p).normalized()*distance; b=p+(after-p).normalized()*distance
        for k in range(9):
            t=k/8; rounded.append(tuple((1-t)**2*a+2*(1-t)*t*p+t*t*b))
    extruded_xz('Glossy rounded lightning bolt',list(reversed(rounded)),.255,M['porcelain'],(0,-.53,-.06),.045)


def helmet():
    # Dome is a continuous ellipsoidal shell with integrated longitudinal stiffeners.
    def dome(t,p,offset=0):
        x=.87*math.sin(t)*math.cos(p); y=1.06*math.sin(t)*math.sin(p)
        z=1.08*math.cos(t)
        u=min(1,max(0,(z-.34)/.26)); env=u*u*(3-2*u)
        ridge=sum(math.exp(-((x-c)/.05)**2) for c in [-.26,0,.26])*.031*env
        z+=ridge
        return (x+offset*math.sin(t)*math.cos(p),y+offset*math.sin(t)*math.sin(p),z+offset*math.cos(t))
    seg,rows=320,96; vs=[]
    # Avoid a ring of coincident vertices at the crown.
    vs.append((0,0,1.111))
    for j in range(1,rows+1):
        for i in range(seg): vs.append(dome((math.pi/2)*j/rows,2*math.pi*i/seg))
    fs=[(0,1+i,1+(i+1)%seg) for i in range(seg)]
    for j in range(rows-1):
        for i in range(seg):
            a=1+j*seg+i; b=1+j*seg+(i+1)%seg; fs.append((a,b,b+seg,a+seg))
    # Parametrisation as t,p has reversed winding; dome must face outward.
    fs=fs[:seg]+[tuple(reversed(f)) for f in fs[seg:]]
    shell=mesh('Hard hat moulded shell',vs,fs,M['white'])
    shell.data.materials.append(M['back'])
    so=shell.modifiers.new('Real shell wall','SOLIDIFY'); so.thickness=.048; so.offset=-1; so.material_offset=1
    b=shell.modifiers.new('Soft base edge','BEVEL'); b.width=.012; b.segments=3
    # Reflective amber film hugs the actual dome, including its curvature.
    stripe=mat('Amber reflective tape D99100','D99100',metal=.3,rough=.25,coat=.45)
    nt=stripe.node_tree; nd=nt.nodes; lk=nt.links
    tc=nd.new('ShaderNodeTexCoord'); noise=nd.new('ShaderNodeTexVoronoi'); noise.feature='DISTANCE_TO_EDGE'; noise.inputs['Scale'].default_value=145
    lk.new(tc.outputs['Generated'],noise.inputs['Vector']); bump=nd.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.12; bump.inputs['Distance'].default_value=.006
    lk.new(noise.outputs['Distance'],bump.inputs['Height']); lk.new(bump.outputs[0],nd.get('Principled BSDF').inputs['Normal'])
    vv=[]; ff=[]
    for j in range(7):
        z=.205+j*.115/6; t=math.acos(z/1.08)
        for i in range(seg): vv.append(dome(t,2*math.pi*i/seg,.006))
    for j in range(6):
        for i in range(seg): a=j*seg+i; b=j*seg+(i+1)%seg; ff.append((a,b,b+seg,a+seg))
    mesh('Continuous amber reflective stripe',vv,ff,stripe)
    # Brim projects further at the front, with a softly rolled leading edge.
    vv=[]; ff=[]
    for j in range(7):
        u=j/6
        for i in range(seg):
            p=2*math.pi*i/seg; front=max(0,-math.sin(p))**5
            x=(.855+.17*u)*math.cos(p); y=(1.045+(.13+.22*front)*u)*math.sin(p)
            z=-.01-.03*u-.07*front*u*u
            vv.append((x,y,z))
    for j in range(6):
        for i in range(seg): a=j*seg+i; b=j*seg+(i+1)%seg; ff.append((a,b,b+seg,a+seg))
    brim=mesh('Swept brim with extended front visor',vv,[tuple(reversed(f)) for f in ff],M['white']); so=brim.modifiers.new('Brim thickness','SOLIDIFY'); so.thickness=.055
    be=brim.modifiers.new('Rolled visor rim','BEVEL'); be.width=.022; be.segments=5
    lip=torus('Continuous white shell-to-brim fillet',(0,0,-.012),1,.024,M['white']); lip.scale=(.87,1.06,1)
    # Inner suspension band, visible below the brim in the turntable.
    vv=[]; ff=[]
    for j in range(2):
        for i in range(seg):
            p=2*math.pi*i/seg; vv.append((.73*math.cos(p),.91*math.sin(p),-.28+.06*math.sin(p)+j*.125))
    for i in range(seg): ff.append((i,(i+1)%seg,(i+1)%seg+seg,i+seg))
    band=mesh('Navy suspension headband',vv,ff,M['ink']); so=band.modifiers.new('Padded band thickness','SOLIDIFY'); so.thickness=.045
    bevel(band,.015,3)
    for side in [-1,1]:
        for yy in [-.45,.48]:
            arm=box('Suspension support',(side*.72,yy,-.15),(.065,.105,.24),M['ink'],.025); arm.rotation_euler[1]=side*.24
        box('Integrated accessory socket',(side*.868,.13,.075),(.1,.30,.20),M['white'],.045)
    cylinder('Rear adjustment dial',(0,.984,-.19),.137,.09,M['ink'],'Y',edge=.016)
    cylinder('Dial satin face',(0,1.033,-.19),.108,.014,M['seam'],'Y',edge=.008)
    for i in range(24):
        a=2*math.pi*i/24
        o=box('Adjustment dial grip',(.137*math.cos(a),.987,-.19+.137*math.sin(a)),(.017,.065,.024),M['ink'],.005); o.rotation_euler[1]=-a


def pose(root,i):
    u=i/29; e=u*u*u*(u*(u*6-15)+10) # Quintic ease, zero velocity and acceleration at both ends.
    root.rotation_euler=(math.radians(2+9*(1-e)), math.radians(-4-8*(1-e)), math.radians(120*(1-e)))

def finish_model(scene,name):
    # Flatten geometry transforms before parenting to one reproducible turntable rig.
    objects=[o for o in scene.objects if o.type in {'MESH','CURVE'}]
    for o in objects:
        if o.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target='MESH')
    objects=[o for o in scene.objects if o.type=='MESH']
    bpy.context.view_layer.update(); deps=bpy.context.evaluated_depsgraph_get(); points=[]
    for o in objects:
        ev=o.evaluated_get(deps); me=ev.to_mesh(); arr=np.empty(len(me.vertices)*3,dtype=np.float64); me.vertices.foreach_get('co',arr)
        ar=arr.reshape(-1,3); mm=np.array(o.matrix_world); ar=ar@mm[:3,:3].T+mm[:3,3]; points.append(ar); ev.to_mesh_clear()
    points=np.concatenate(points); centre=(points.min(0)+points.max(0))/2
    root=bpy.data.objects.new(name+' • turntable rig',None); scene.collection.objects.link(root)
    for o in objects:
        o.location-=Vector(centre); o.parent=root
    points-=centre
    cam_basis=np.array(scene.camera.rotation_euler.to_matrix()); right=cam_basis[:,0]; up=cam_basis[:,1]
    poses=[]
    for i in range(30):
        pose(root,i); rot=np.array(root.rotation_euler.to_matrix()); q=points@rot.T
        xy=np.stack((q@right,q@up),axis=1); poses.append((xy.min(0),xy.max(0)))
    hmin,hmax=poses[-1]
    hero_span=max(hmax-hmin)
    maximum_span=max(float(np.max(hi-lo)) for lo,hi in poses)
    scale=min(4.8*.80/hero_span,4.8*.90/maximum_span)
    root.scale=(scale,)*3
    for i in range(30):
        pose(root,i)
        # Small image-plane drift centres the rotating silhouette, like a flying product.
        lo,hi=poses[i]; centre2d=(lo+hi)/2
        root.location=Vector((-centre2d[0]*right-centre2d[1]*up)*scale)
        root.keyframe_insert('rotation_euler',frame=i)
        root.keyframe_insert('location',frame=i)
    scene.frame_start=0; scene.frame_end=29; scene.frame_set(29)
    root['turn_degrees']=120; root['easing']='quintic smoothstep'; root['frame_29_is_hero']=True
    scene['asset_provenance']='AI-made: original procedural 3D modelling by gpt-6-astra in Blender. No downloaded geometry, textures or HDRIs.'
    scene['model_name']=name; scene['rig_scale']=scale
    bpy.context.view_layer.update()
    print('FRAMING',name,'hero_span',hero_span*scale/4.8,'max_span',maximum_span*scale/4.8,flush=True)
    return root


def run(name):
    scene=setup(); globals()[name](); root=finish_model(scene,name)
    scene.render.resolution_x=scene.render.resolution_y=1024
    if ARGS.engine=='CYCLES': scene.cycles.samples=ARGS.hero_samples
    # The editable scene is part of the deliverable; Blender backup files disabled.
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
    measurements=[]
    def render(path,res,samples,frame):
        scene.frame_set(frame); scene.render.resolution_x=scene.render.resolution_y=res
        if ARGS.engine=='CYCLES': scene.cycles.samples=samples
        scene.render.filepath=str(path); t=time.perf_counter(); bpy.ops.render.render(write_still=True)
        seconds=time.perf_counter()-t; measurements.append({'path':str(path.relative_to(OUT)),'seconds':round(seconds,3),'size':res,'samples':samples})
        print('ASSET_FRAME',name,frame,res,round(seconds,3),flush=True)
    if ARGS.mode in ['heroes','all']: render(OUT/(name+'_hero.png'),1024,ARGS.hero_samples,29)
    if ARGS.mode in ['spin','all']:
        d=OUT/(name+'_spin'); d.mkdir(exist_ok=True)
        for i in range(30): render(d/('%04d.png'%i),512,ARGS.samples,i)
    (OUT/(name+'_timing_'+ARGS.mode+'.json')).write_text(json.dumps({'object':name,'engine':ARGS.engine,'frames':measurements},indent=2)+'\n')
    print('ASSET_FINISHED',name,flush=True)

for name in ARGS.objects: run(name)
