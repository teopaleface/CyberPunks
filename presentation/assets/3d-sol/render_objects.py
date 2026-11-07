"""Procedural, original 3D models for Tura de maine. Blender 5.2.1.

No external textures, meshes, fonts, or internet assets. All outputs stay beside
this script. The presentation reference PNGs are visual references, not textures.
"""
import bpy
import math
import argparse
import json
import sys
import time
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

OUT = Path(__file__).resolve().parent
NAMES = ("meter", "transformer", "solar", "storm", "helmet")
parser = argparse.ArgumentParser()
parser.add_argument("--objects", nargs="+", default=list(NAMES), choices=NAMES)
parser.add_argument("--mode", choices=("hero", "spin", "all"), default="all")
parser.add_argument("--device", choices=("metal", "cpu"), default="metal")
parser.add_argument("--hero-samples", type=int, default=64)
parser.add_argument("--spin-samples", type=int, default=32)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def rgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c)


def mat(name, color, rough=.25, metal=0, coat=.25):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb(color), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = .16
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def assign(o, m):
    o.data.materials.append(m)
    return o


def bevel(o, width=.04, segments=5, normals=True):
    b = o.modifiers.new("Precision radiused edges", "BEVEL")
    b.width = width
    b.segments = segments
    b.harden_normals = True
    if normals:
        w = o.modifiers.new("Planar face normals", "WEIGHTED_NORMAL")
        w.keep_sharp = True
        w.weight = 40
    return o


def box(name, loc, size, m, radius=.04, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(o, radius, 8 if radius > .1 else 5)
    smooth(o)
    assign(o, m)
    if rotation is not None:
        o.rotation_euler = rotation
    return o


def cyl(name, loc, radius, depth, m, rotation=None, vertices=96, edge=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    if edge:
        bevel(o, edge, 4)
    smooth(o)
    assign(o, m)
    if rotation is not None:
        o.rotation_euler = rotation
    return o


def sphere(name, loc, scale, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=80, ring_count=48, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(o)
    assign(o, m)
    return o


def ring(name, loc, major, minor, m, rotation=None, scale=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=96, minor_segments=16,
        location=loc, major_radius=major, minor_radius=minor)
    o = bpy.context.object
    o.name = name
    if rotation:
        o.rotation_euler = rotation
    if scale:
        o.scale = scale
    smooth(o)
    assign(o, m)
    return o


def mesh(name, verts, faces, m, edge=0, shading=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    assign(o, m)
    if shading:
        smooth(o)
    if edge:
        bevel(o, edge, 6)
    return o


def panel(name, loc, width, height, depth, radius, m, edge=.012):
    """Rounded XZ silhouette independent of its shallow Y extrusion thickness."""
    outline=[]
    for cx,cz,start in ((width/2-radius,height/2-radius,0),
                        (-width/2+radius,height/2-radius,90),
                        (-width/2+radius,-height/2+radius,180),
                        (width/2-radius,-height/2+radius,270)):
        for i in range(17):
            a=math.radians(start+90*i/16)
            outline.append((cx+radius*math.cos(a),cz+radius*math.sin(a)))
    n=len(outline)
    x0,y0,z0=loc
    verts=[(x0+x,y0+y,z0+z) for y in (-depth/2,depth/2) for x,z in outline]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return mesh(name,verts,faces,m,edge)


def beam(name, a, b, width, depth, m, radius=.025):
    a, b = Vector(a), Vector(b)
    o = box(name, (a+b)/2, (width, depth, (b-a).length), m, radius)
    o.rotation_euler = (b-a).to_track_quat("Z", "Y").to_euler()
    return o


def lathe(name, center, profile, m, sides=96):
    verts = []
    for z, r in profile:
        for i in range(sides):
            a = 2*math.pi*i/sides
            verts.append((center[0]+r*math.cos(a), center[1]+r*math.sin(a), center[2]+z))
    faces = []
    for j in range(len(profile)-1):
        for i in range(sides):
            k = (i+1) % sides
            faces.append((j*sides+i, j*sides+k, (j+1)*sides+k, (j+1)*sides+i))
    faces.extend([tuple(range(sides-1, -1, -1)), tuple((len(profile)-1)*sides+i for i in range(sides))])
    return mesh(name, verts, faces, m)


def screw(name, loc, r=.035, face=False):
    rot = (math.pi/2, 0, 0) if face else None
    cyl(name, loc, r, .026, M["steel"], rot, vertices=48, edge=.006)
    x, y, z = loc
    if face:
        box(name+" slot A", (x, y-.014, z), (r*1.2, .003, .008), M["ink"], .003)
        box(name+" slot B", (x, y-.014, z), (.008, .003, r*1.2), M["ink"], .003)


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = args.spin_samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = .025
    sc.cycles.seed = 22
    sc.cycles.use_animated_seed = False
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 8
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 25
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -.20
    sc.view_settings.gamma = 1
    sc.render.use_file_extension = True
    sc.render.use_persistent_data = True
    sc.world = bpy.data.worlds.new("Neutral white studio environment")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = .80
    device = "CPU"
    if args.device == "metal":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            gpu = [d for d in prefs.devices if d.type == "METAL"]
            if not gpu:
                raise RuntimeError("No Metal device exposed by Blender")
            for d in prefs.devices:
                d.use = d.type == "METAL"
            sc.cycles.device = "GPU"
            device = ", ".join(d.name for d in gpu)
        except Exception as exc:
            print("Metal unavailable, CPU fallback:", str(exc), flush=True)
            sc.cycles.device = "CPU"
    else:
        sc.cycles.device = "CPU"
    bpy.ops.object.camera_add(location=(7, -11, 6.7))
    camera = bpy.context.object
    camera.name = "Shared orthographic studio camera"
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 5.6
    camera.data.lens = 65
    sc.camera = camera
    def area(name, loc, power, size, target=(0, 0, 0), size_y=None):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = power
        data.shape = "RECTANGLE"
        data.size = size
        data.size_y = size_y or size
        o = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target)-o.location).to_track_quat("-Z", "Y").to_euler()
    area("Large softbox upper left", (-3.8, -4.5, 6), 100, 4, size_y=5)
    area("Right pearl fill", (4, -2, 2.8), 50, 3, size_y=5)
    area("Back edge softbox", (2.5, 4, 5), 100, 3, size_y=4)
    area("Vertical metal reflection", (-4, .3, 1.2), 30, 1.2, size_y=4)
    bpy.context.view_layer.update()
    return device


def materials():
    global M
    M = {
        "white": mat("Pearl white molded polymer", "F4F6FA", .26, .015, .22),
        "ceramic": mat("Glazed white ceramic", "F8F9FC", .22, .015, .25),
        "steel": mat("Satin silver machined metal", "C4CED8", .25, .78, .16),
        "tank": mat("Satin pale aluminium", "C9D0D7", .28, .58, .16),
        "gasket": mat("Soft pale grey seam", "CAD1D9", .39, .05, .10),
        "ink": mat("Ink navy 0B1622", "0B1622", .25, .18, .28),
        "amber": mat("Amber enamel F2A20C", "F2A20C", .2, .12, .5),
        "roof": mat("Midnight blue glazed roof tiles", "142334", .27, .16, .38),
    }
    concrete = mat("Fine pale concrete", "D9DCDF", .64, 0, .04)
    ns, ls = concrete.node_tree.nodes, concrete.node_tree.links
    no = ns.new("ShaderNodeTexNoise")
    no.inputs["Scale"].default_value = 105
    no.inputs["Detail"].default_value = 2
    bump = ns.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .17
    bump.inputs["Distance"].default_value = .024
    ls.new(no.outputs["Fac"], bump.inputs["Height"])
    ls.new(bump.outputs["Normal"], ns.get("Principled BSDF").inputs["Normal"])
    M["concrete"] = concrete


def meter():
    frontrot = (math.pi/2, 0, 0)
    box("Rounded meter rear shell", (0, .035, 1.5), (2.02, .68, 2.70), M["white"], .21)
    box("Fine shell perimeter seam", (0, -.252, 1.5), (1.985, .135, 2.65), M["gasket"], .205)
    panel("Main white instrument cover", (0, -.303, 1.81), 1.98, 2.01, .185, .20, M["white"], .028)
    panel("Separate sealed terminal cover", (0, -.305, .49), 1.98, .63, .19, .15, M["white"], .028)
    panel("Deep ink screen bezel", (0, -.410, 2.045), 1.65, 1.00, .082, .16, M["ink"], .022)
    ring("Tactile button polished rim", (.60, -.428, 1.222), .123, .018, M["steel"], frontrot)
    cyl("Satin circular button", (.60, -.438, 1.222), .107, .035, M["steel"], frontrot, edge=.012)
    screen = mat("Blue screen optical glow 2364D2", "2364D2", .18, .05, .5)
    nt = screen.node_tree
    ns, ls = nt.nodes, nt.links
    tc = ns.new("ShaderNodeTexCoord")
    sep = ns.new("ShaderNodeSeparateXYZ")
    ls.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = ns.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements.remove(cr.elements[1])
    for idx, (pos, col) in enumerate(((0, "10243D"), (.5, "2364D2"), (1, "12377A"))):
        e = cr.elements[0] if idx == 0 else cr.elements.new(pos)
        e.position = pos
        e.color = (*rgb(col), 1)
    ls.new(sep.outputs["Z"], ramp.inputs[0])
    p = ns.get("Principled BSDF")
    ls.new(ramp.outputs[0], p.inputs["Base Color"])
    ls.new(ramp.outputs[0], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = .22
    panel("Inset optical blue display", (0, -.457, 2.045), 1.395, .744, .024, .11, screen, .008)
    led = mat("Blue status light", "2364D2", .19, .1, .4)
    p = led.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value = (*rgb("2364D2"), 1)
    p.inputs["Emission Strength"].default_value = .4
    cyl("Small status indicator", (-.66, -.404, 1.212), .026, .016, led, frontrot, edge=.006)
    for x in (-.72, .72):
        screw("Terminal cover security screw", (x, -.408, .50), .044, True)
    # Functional reverse side, visible during the turn, not a hollow image plane.
    box("Recessed back mounting pad", (0, .387, 1.46), (1.45, .10, 1.93), M["gasket"], .12)
    for x in (-.54, .54):
        box("Back mounting rail", (x, .466, 1.53), (.13, .12, 1.66), M["white"], .035)
        for z in (.92, 2.16):
            box("Back rail recessed slot", (x, .534, z), (.055, .008, .14), M["ink"], .024)
    for x in (-.53, -.27, 0, .27, .53):
        box("Bottom cable entry", (x, .03, .168), (.145, .28, .026), M["gasket"], .04)


def transformer():
    cyl("Short concrete pole section", (-.98, .40, 1.70), .215, 3.40, M["concrete"], edge=.035)
    # Back mounting straps and true diagonal support.
    for z in (.64, 2.02):
        ring("Pole mounting steel strap", (-.98, .40, z), .225, .026, M["steel"])
        box("Pole bracket front plate", (-.98, .142, z), (.35, .12, .21), M["steel"], .028)
        screw("Bracket bolt", (-.98, .068, z), .053, True)
        box("Horizontal tank mounting beam", (-.42, .35, z), (1.1, .16, .14), M["steel"], .03)
    beam("Diagonal structural brace", (-.98, .30, .30), (-.03, .30, .66), .13, .15, M["steel"])
    box("Vertical back mounting rail", (-.98, .265, 1.24), (.15, .17, 1.94), M["steel"], .025)
    cx, cy = .15, -.08
    cyl("Rounded cylindrical transformer tank", (cx, cy, 1.40), .655, 1.53, M["tank"], edge=.065)
    for i in range(22):
        a = i*2*math.pi/22
        o = box("Rounded cooling radiator fin %02d" % i,
            (cx+.686*math.cos(a), cy+.686*math.sin(a), 1.40),
            (.28, .055, 1.20), M["tank"], .026, (0, 0, a))
    cyl("Lower rolled tank rim", (cx, cy, .655), .677, .095, M["tank"], edge=.035)
    cyl("Top lid flange", (cx, cy, 2.19), .775, .115, M["steel"], edge=.034)
    cyl("Domed pale tank lid", (cx, cy, 2.25), .728, .095, M["tank"], edge=.044)
    for i in range(12):
        a = 2*math.pi*i/12
        cyl("Hexagonal lid fastener", (cx+.697*math.cos(a), cy+.697*math.sin(a), 2.268),
            .035, .044, M["steel"], vertices=6, edge=.005)
    for j, x in enumerate((-.36, .15, .66)):
        y = -.08
        cyl("Bushing silver base flange", (x, y, 2.335), .163, .065, M["steel"], edge=.016)
        profile = [(0, .098), (.06, .098)]
        for k in range(3):
            zz = .07+k*.145
            profile += [(zz, .098), (zz+.025, .13), (zz+.045, .195),
                        (zz+.062, .202), (zz+.078, .192),
                        (zz+.10, .126), (zz+.128, .098)]
        profile += [(.515, .095), (.55, .072)]
        lathe("Glazed ceramic three-skirt insulator %d" % (j+1), (x, y, 2.36), profile, M["ceramic"])
        cyl("Terminal collar", (x, y, 2.928), .074, .07, M["steel"], edge=.01)
        cyl("Terminal hex nut", (x, y, 2.986), .064, .055, M["steel"], vertices=6, edge=.006)
        cyl("Terminal threaded stud", (x, y, 3.06), .035, .11, M["steel"], vertices=48, edge=.008)
        for k in range(5):
            ring("Terminal thread", (x, y, 3.023+k*.017), .035, .004, M["steel"])
    cyl("Bottom drain fitting", (.45, -.08, .55), .066, .14, M["steel"], vertices=6, edge=.012)


def solar():
    width, depth, peak, eave = 2.5, .90, 1.03, .40
    slope = (peak-eave)/depth
    angle = math.atan(slope)
    # Solid white gable / fascia under the tile layer.
    verts = [(-1.25,-depth,eave-.13), (1.25,-depth,eave-.13),
             (-1.25,0,peak-.13), (1.25,0,peak-.13),
             (-1.25,depth,eave-.13), (1.25,depth,eave-.13),
             (-1.25,-depth,eave), (1.25,-depth,eave),
             (-1.25,0,peak), (1.25,0,peak),
             (-1.25,depth,eave), (1.25,depth,eave)]
    faces = [(0,2,3,1),(2,4,5,3),(6,7,9,8),(8,9,11,10),
             (0,1,7,6),(4,10,11,5),(0,6,8,10,4,2),(1,3,5,11,9,7)]
    mesh("White solid roof section", verts, faces, M["white"], .035)
    for x in (-1.255, 1.255):
        for sign in (-1, 1):
            beam("White gable fascia", (x, sign*.94, .34), (x, 0, .99), .115, .12, M["white"], .045)
    for sign in (-1, 1):
        box("White eaves fascia", (0, sign*.94, .33), (2.62, .14, .16), M["white"], .055)
        for row in range(3):
            for col in range(7):
                x0 = -1.25+col*(2.5/7)
                ya = .02+row*.30
                yb = ya+.333
                vs, fs = [], []
                for jj in range(5):
                    yy = ya+(yb-ya)*jj/4
                    for ii in range(17):
                        xx = x0+(2.5/7)*ii/16
                        wave = .035*(.5+.5*math.cos(2*math.pi*ii/16))
                        zz = peak-slope*yy+.025+wave+(2-row)*.012
                        vs.append((xx, sign*yy, zz))
                for jj in range(4):
                    for ii in range(16):
                        a = jj*17+ii
                        q = (a,a+1,a+18,a+17)
                        fs.append(q if sign > 0 else q[::-1])
                o = mesh("Individual navy roof tile", vs, fs, M["roof"])
                solid = o.modifiers.new("Tile thickness", "SOLIDIFY")
                solid.thickness = .028
                bevel(o, .012, 3, False)
    # A panel is modelled flat in its own local frame, then tilted onto the roof.
    panel_objects = set(bpy.context.scene.objects)
    box("Machined silver solar frame", (0,0,0), (2.21,1.26,.105), M["steel"], .047)
    box("Pale panel encapsulation bed", (0,0,.052), (2.105,1.155,.018), M["white"], .036)
    for row in range(3):
        for col in range(4):
            cm = mat("Monocrystalline cell %d %d" % (row,col),
                     ("122B49", "142F50", "152E4C")[(col+row)%3], .16, .05, .48)
            x = (col-1.5)*.516
            y = (row-1)*.376
            box("Rounded photovoltaic silicon cell", (x,y,.067), (.498,.354,.012), cm, .027)
            for k in (-1, 0, 1):
                box("Fine silver cell busbar", (x+k*.115,y,.075), (.003,.315,.002), M["steel"], .0008)
    for x in (-.67, .67):
        box("Solar lower mounting bracket", (x,-.69,-.035), (.15,.30,.048), M["steel"], .022)
        cyl("Solar bracket fastener", (x,-.77,-.006), .043, .027, M["steel"], vertices=6, edge=.008)
    new = [o for o in bpy.context.scene.objects if o not in panel_objects]
    bpy.context.view_layer.update()
    R = Matrix.Rotation(angle, 4, "X")
    T = Matrix.Translation((0,-.40,.40+slope*.50+.17))
    for o in new:
        o.matrix_world = T @ R @ o.matrix_world
    # Glossy solid amber sphere, intentionally behind the upper-right panel corner.
    sphere("Glossy amber sun sphere", (.90,.39,1.48), (.46,.46,.46), M["amber"])


def storm():
    cloud = mat("Cloud white to plum underside A23C9E", "F4F6FA", .25, .025, .32)
    ns, ls = cloud.node_tree.nodes, cloud.node_tree.links
    tc = ns.new("ShaderNodeTexCoord")
    sep = ns.new("ShaderNodeSeparateXYZ")
    ramp = ns.new("ShaderNodeValToRGB")
    ls.new(tc.outputs["Generated"], sep.inputs[0])
    ls.new(sep.outputs["Z"], ramp.inputs[0])
    stops = ((0,"A23C9E"),(.20,"A23C9E"),(.48,"C8A3CD"),(.68,"F4F6FA"),(1,"F4F6FA"))
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(p,c) in enumerate(stops):
        e = ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(p)
        e.position = p
        e.color = (*rgb(c),1)
    ls.new(ramp.outputs[0], ns.get("Principled BSDF").inputs["Base Color"])
    parts = [sphere("Cloud upper volume", (0,.04,.98), (.69,.46,.74), cloud),
             sphere("Cloud left volume", (-.69,0,.51), (.60,.48,.55), cloud),
             sphere("Cloud right volume", (.66,.015,.51), (.65,.48,.57), cloud),
             sphere("Cloud lower joining volume", (0,-.015,.50), (.94,.47,.49), cloud)]
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = "Seamless sculpted cloud, watertight 3D volume"
    rem = o.modifiers.new("Union the soft cloud volumes", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = .027
    rem.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm = o.modifiers.new("Soft sculpt relaxation", "SMOOTH")
    sm.factor = 1.1
    sm.iterations = 28
    sub = o.modifiers.new("Subpixel cloud curvature", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    smooth(o)
    poly = [(-.08,.43),(.48,.43),(.14,-.12),(.52,-.12),(-.30,-1.09),(-.14,-.39),(-.49,-.39)]
    verts = [(x,y,z) for y in (-.65,-.40) for x,z in poly]
    n = len(poly)
    faces = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh("Solid rounded white lightning bolt", verts, faces, M["white"], .055)


def helmet():
    nphi, nt = 160, 56
    rx, ry, h, base = .98, 1.11, 1.20, .26
    vs, fs = [], []
    for j in range(nt+1):
        t = .0002+(math.pi/2-.0002)*j/nt
        r = math.sin(t)**.92
        z = base+h*max(0,math.cos(t))**.8
        for i in range(nphi):
            p = 2*math.pi*i/nphi
            vs.append((rx*r*math.cos(p),ry*r*math.sin(p),z))
    for j in range(nt):
        for i in range(nphi):
            k=(i+1)%nphi
            fs.append((j*nphi+i,(j+1)*nphi+i,(j+1)*nphi+k,j*nphi+k))
    o = mesh("Continuous molded white hard-hat shell", vs, fs, M["white"])
    sol=o.modifiers.new("Real hollow shell thickness", "SOLIDIFY")
    sol.thickness=.055
    bevel(o,.018,4,False)
    # Curved visor / brim, with an extended front rather than a flat disc.
    vs, fs=[],[]
    for j in range(9):
        f=j/8
        for i in range(nphi):
            p=2*math.pi*i/nphi
            forward=max(0,-math.sin(p))**6
            x=(rx-.025+f*.19)*math.cos(p)
            y=(ry-.025+f*(.19+.36*forward))*math.sin(p)
            z=.265-.08*f-.085*forward*f**1.5
            vs.append((x,y,z))
    for j in range(8):
        for i in range(nphi):
            k=(i+1)%nphi
            fs.append((j*nphi+i,(j+1)*nphi+i,(j+1)*nphi+k,j*nphi+k))
    o=mesh("Swept front visor and rounded perimeter brim",vs,fs,M["white"])
    sol=o.modifiers.new("Visor thickness", "SOLIDIFY")
    sol.thickness=.055
    bevel(o,.022,5,False)
    # Reflective amber band follows the curved dome without intersecting it.
    stripe=mat("Reflective amber helmet stripe F2A20C", "F2A20C", .24,.12,.42)
    ns,ls=stripe.node_tree.nodes,stripe.node_tree.links
    tc=ns.new("ShaderNodeTexCoord")
    vor=ns.new("ShaderNodeTexVoronoi")
    vor.feature="DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value=125
    ls.new(tc.outputs["Generated"],vor.inputs["Vector"])
    bump=ns.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.12
    bump.inputs["Distance"].default_value=.004
    ls.new(vor.outputs["Distance"],bump.inputs["Height"])
    ls.new(bump.outputs["Normal"],ns.get("Principled BSDF").inputs["Normal"])
    vs,fs=[],[]
    for j in range(9):
        z=.425+.157*j/8
        t=math.acos(((z-base)/h)**(1/.8))
        r=math.sin(t)**.92+.004
        for i in range(nphi):
            p=2*math.pi*i/nphi
            vs.append((rx*r*math.cos(p),ry*r*math.sin(p),z))
    for j in range(8):
        for i in range(nphi):
            k=(i+1)%nphi
            fs.append((j*nphi+i,j*nphi+k,(j+1)*nphi+k,(j+1)*nphi+i))
    mesh("Continuous curved amber safety band",vs,fs,stripe)
    # Two broad molded ribs blend into the shell. No faceted polygon ridges.
    for cx in (-.235,.235):
        vs,fs=[],[]
        for j in range(81):
            y=-.97+1.94*j/80
            taper=math.sin(math.pi*j/80)**.55
            for i in range(13):
                cross=-1+2*i/12
                x=cx+cross*.065
                dome=max(0,1-(x/rx)**2-(y/ry)**2)
                z=base+h*dome**.4+.054*(1-cross*cross)**2*taper+.002
                vs.append((x,y,z))
        for j in range(80):
            for i in range(12):
                a=j*13+i
                fs.append((a,a+1,a+14,a+13))
        mesh("Raised molded longitudinal shell rib",vs,fs,M["white"])
    ring("Dark navy padded internal headband",(0,0,.19),.83,.064,M["ink"],scale=(1,1.18,1))
    for side in (-1,1):
        for y in (-.52,.52):
            box("White accessory mounting lug",(side*.944,y,.328),(.14,.24,.16),M["white"],.045)
        beam("Suspension support",(side*.78,.44,.17),(side*.60,.55,-.08),.09,.075,M["ink"],.03)
    box("Rear navy fit adjustment carrier",(0,.98,.085),(.79,.16,.19),M["ink"],.065)
    cyl("Rear fit adjustment wheel",(0,1.09,.085),.115,.07,M["ink"],(math.pi/2,0,0),edge=.022)


BUILDERS = dict(zip(NAMES, (meter, transformer, solar, storm, helmet)))


def pose(t):
    # Quintic ease in/out: zero velocity AND acceleration at both ends.
    e = 6*t**5-15*t**4+10*t**3
    return (math.radians(-6)*(1-e), math.radians(9)*(1-e), math.radians(120)*(1-e))


def fit_and_parent(name):
    """Fit evaluated 3D vertices at ALL 30 poses, not just an origin/bounding box.

    Hero occupies 80% if possible. Every turn retains >=7% projected margin.
    All models share a fixed 5.6-unit ortho camera and the same studio lights.
    """
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    coords=[]
    for o in objects:
        ev=o.evaluated_get(dg)
        me=ev.to_mesh()
        a=np.empty(len(me.vertices)*3,dtype=np.float64)
        me.vertices.foreach_get("co",a)
        a=a.reshape((-1,3))
        m=np.array(ev.matrix_world)
        coords.append(a @ m[:3,:3].T+m[:3,3])
        ev.to_mesh_clear()
    pts=np.concatenate(coords)
    center=(pts.min(axis=0)+pts.max(axis=0))/2
    bpy.ops.object.empty_add(type="PLAIN_AXES",location=(0,0,0))
    root=bpy.context.object
    root.name=name+" complete 3D turntable root"
    for o in objects:
        o.parent=root
        o.location-=Vector(center)
    pts-=center
    camera=bpy.context.scene.camera
    basis=np.array(camera.rotation_euler.to_matrix())
    right,up=basis[:,0],basis[:,1]
    hero=np.column_stack((pts @ right,pts @ up))
    hero_span=(hero.max(axis=0)-hero.min(axis=0)).max()
    scale=5.6*.80/hero_span
    placements=[]
    for i in range(30):
        from mathutils import Euler
        rot=np.array(Euler(pose(i/29),"XYZ").to_matrix())
        pp=pts @ rot.T
        uv=np.column_stack((pp @ right,pp @ up))
        span=(uv.max(axis=0)-uv.min(axis=0)).max()
        mid=(uv.min(axis=0)+uv.max(axis=0))/2
        s=min(scale,5.6*.86/span)
        location=-s*(right*mid[0]+up*mid[1])
        placements.append((s,location.tolist(),span))
    info={"uniform_scale":scale,"hero_fill_estimate":scale*hero_span/5.6,
          "minimum_projected_margin_px_at_512":min(512*(.5-s*span/5.6/2) for s,_,span in placements),
          "framing_scale_range":[min(s for s,_,_ in placements),max(s for s,_,_ in placements)]}
    return root,info,placements


def apply_pose(root,index,placements):
    s,loc,_=placements[index]
    root.rotation_euler=pose(index/29)
    root.scale=(s,s,s)
    root.location=loc


def render(path, size, samples):
    sc=bpy.context.scene
    sc.render.resolution_x=size
    sc.render.resolution_y=size
    sc.cycles.samples=samples
    sc.render.filepath=str(path)
    start=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    duration=time.perf_counter()-start
    print("RENDER_TIME",path.name,round(duration,3),flush=True)
    return duration


for name in args.objects:
    build_start=time.perf_counter()
    device=setup()
    materials()
    BUILDERS[name]()
    root,info,placements=fit_and_parent(name)
    report={"object":name,"engine":"Cycles","device":device,
            "hero_samples":args.hero_samples,"spin_samples":args.spin_samples,
            "color_transform":"Standard","exposure":-.20,"transparent":True,
            "camera_location":[7,-11,6.7],"camera_ortho_scale":5.6,
            "rotation_degrees":120,"frames":30,"easing":"quintic smootherstep",
            **info,"build_and_fit_seconds":time.perf_counter()-build_start}
    apply_pose(root,29,placements)
    if args.mode in ("hero","all"):
        report["hero_seconds"]=render(OUT/(name+"_hero.png"),1024,args.hero_samples)
    if args.mode in ("spin","all"):
        folder=OUT/(name+"_spin")
        folder.mkdir(exist_ok=True)
        times=[]
        for i in range(30):
            apply_pose(root,i,placements)
            times.append(render(folder/("%04d.png"%i),512,args.spin_samples))
        report["spin_seconds"]=times
        report["spin_mean_seconds"]=sum(times)/len(times)
        report["spin_median_seconds"]=float(np.median(times))
    previous=OUT/(name+"_render_metrics.json")
    if previous.exists():
        old=json.loads(previous.read_text())
        old.update(report)
        report=old
    previous.write_text(json.dumps(report,indent=2)+"\n")
    print("OBJECT_COMPLETE",name,json.dumps(report),flush=True)
