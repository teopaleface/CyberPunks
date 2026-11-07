from pathlib import Path
p=Path(__file__).resolve().with_name('build_planet.py'); s=p.read_text()
s=s.replace("exec(compile(source,str(base),'exec'),globals())", """# A small, organic hero village on the front cap. Other original houses continue on the far side.
hero=[(-6.4,-.6),(-5.1,-3.4),(-2.9,-5.4),(-.7,-6.3),(4.7,3.3),(6.3,.4),(5.,-4.8),(-1.1,6.2),(2.6,5.8)]
back=[(x,y) for y in [-7.8,-3.7,.5,4.6,8.2] for x in [-23,-19.7,-16.3,16.3,19.7,23]][:30]
planet_layout=hero+back
start=source.index('houses=[]'); end=source.index('# Field board',start)
source=source[:start]+'''houses=[]
for i,(xx,yy) in enumerate(planet_layout):
    x=xx+random.uniform(-.08,.08); y=yy/.72+random.uniform(-.08,.08)
    house(x,y,random.uniform(1.22,1.64),random.uniform(1.5,2.03),random.uniform(.90,1.20),annex=i%6==0)
    houses.append((x,y))
    if i%3==0: tree(x+1.0,y+.8,random.uniform(.65,.9))
'''+source[end:]
start=source.index('pin_specs=['); end=source.index('pins=[]',start)
source=source[:start]+'''pin_specs=[(0,-.7,-6.3/.72,.4),(0,5,-4.8/.72,.7),(0,-1.1,6.2/.72,.95),(1,6.3,.4/.72,.4),(1,4.7,3.3/.72,.7),(1,2.6,5.8/.72,.95),(2,-6.4,-.6/.72,.4),(2,-5.1,-3.4/.72,.7),(2,-2.9,-5.4/.72,.95)]
'''+source[end:]
exec(compile(source,str(base),'exec'),globals())""")
s=s.replace('S=.04; R=14.; LAT=.32','S=.04; R=8.; LAT=.18')
# Clear the old road poles and the rectangular-grid tethers.
mark='def color(h):'
s=s.replace(mark,"""for o in list(COL['village'].objects):
    if o.name.startswith(('Concrete distribution','White crossarm','Porcelain insulator','Suspended dark')): bpy.data.objects.remove(o,do_unlink=True)
for o in list(COL['routes'].objects):
    if o.name.startswith('House tether'): bpy.data.objects.remove(o,do_unlink=True)
"""+mark)
s=s.replace("for x,y,sc in [(-10.4,2.4,1.28),(-10.4,5.6,1.15),(-.3,1.7,1.15),(6.7,-5.7,1.08),(8.3,6.7,1.2)]", "for x,y,sc in [(-1.8,2.7,1.25),(.2,3.8,1.2),(1.8,1.7,1.13),(-3.4,-.1,.9),(5.8,5.1,.9)]")
s=s.replace("w,d,h=o.dimensions; nx=", "w,d,h=[max(v.co[a] for v in o.data.vertices)-min(v.co[a] for v in o.data.vertices) for a in range(3)]; nx=")
# Canonical street-following paths in the new hand-made layout.
a=s.index("for o in list(COL['depot'].objects):\n    if o.name.startswith('Depot raised yard')"); b=s.index('# The depot is now',a)
s=s[:a]+"""for o in list(COL['depot'].objects):
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
        for j in range(5): vs.append(tuple(pt+side*(-1+j*.5)))
    for i in range(len(dense)-1):
        for j in range(4): a=i*5+j; fs.append((a,a+1,a+6,a+5))
    ob=mesh(name,vs,fs,material)
    for p in ob.data.polygons: p.use_smooth=True
    return ob
active=COL['village']
for i,points in enumerate(new_paths): strip_path('Winding rural asphalt road',[(x,y,.21) for x,y,z in points],1.18 if i==0 else 1.0,ASPHALT if i==0 else GRAVEL)
for x,y in [(-6.8,1.4),(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8),(1,-5.7)]:
    before=set(active.objects); pole(x,y)
    for ob in set(active.objects)-before:
        if ob.type=='MESH': ob.data.materials.clear(); ob.data.materials.append(IVORY if 'insulator' in ob.name else CONCRETE)
for (x1,y1),(x2,y2) in zip([(-6.8,1.4),(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8)],[(-3.7,1.5),(-.6,.8),(-.3,-1.6),(1,-3.8),(1,-5.7)]):
    for off in [-.25,0,.25]: curve('Fine curved rural distribution wire',[(x1+off,y1,2.7),((x1+x2)/2+off,(y1+y2)/2,2.45),(x2+off,y2,2.7)],.009,WIRE,True)
"""+s[b:]
# Fresh ribbons on the same roads.
a=s.index("for o in list(COL['routes'].objects):\n    if not o.name.startswith('Route ')"); b=s.index('# Put the three route trucks',a)
s=s[:a]+"""for o in list(COL['routes'].objects):
    if o.name.startswith('Route '): bpy.data.objects.remove(o,do_unlink=True)
active=COL['routes']
for i,(points,material) in enumerate(zip(new_paths,[PPC,CYAN,ELECTRIC])):
    ribbon=strip_path('Route %d | satin road ribbon'%i,[(x,y,.25) for x,y,z in points],.31,material)
    solid=ribbon.modifiers.new('Satin tape thickness','SOLIDIFY'); solid.thickness=.008
scene['route_paths']=json.dumps(new_paths)
"""+s[b:]
s=s.replace("[-18.5,-17,-15.5]", "[-18.5,-17,-15.5]")
# Place the meter and panels on two hero houses.
s=s.replace("(-3.35,1.92,.82)","(-6.4,-1.24,.82)").replace("(-3.35,1.825,.85),(-3.35,1.805,.85)","(-6.4,-1.325,.85),(-6.4,-1.345,.85)")
s=s.replace("-3.05+.13*math.cos", "-6.10+.13*math.cos").replace("1.78,.72-.13", "-1.37,.72-.13")
s=s.replace("panel.location=(-6.49,2.63,1.78)","panel.location=(-5.44,-3.4,1.78)")
s=s.replace("worker('Roof inspection crew',-5.25,1.45", "worker('Roof inspection crew',-4.4,-4.2")
# Before baking, move the original depot coherently and place the field in the foreground.
mark='# Terrain is a proper closed spherical surface'
s=s.replace(mark,"""# The existing depot is one coherent small campus at the top-left of the village.
bpy.context.view_layer.update()
depot_T=Matrix.Translation(Vector((-4.5,3.2,0)))@Matrix.Rotation(.10,4,'Z')@Matrix.Diagonal((.72,.72,.72,1))@Matrix.Translation(Vector((15,3,0)))
for ob in list(COL['depot'].objects)+list(COL['parked'].objects):
    if ob.parent is None: ob.matrix_world=depot_T@ob.matrix_world
for ob in COL['details'].objects:
    if ob.parent is None and (ob.name.startswith(('Depot crew','Coffee thermos','Dog'))): ob.matrix_world=depot_T@ob.matrix_world
field_T=Matrix.Translation(Vector((3.8,-2,0)))@Matrix.Diagonal((.65,.65,1,1))@Matrix.Translation(Vector((17,-7.2,0)))
for ob in COL['village'].objects:
    if ob.name.startswith(('Sunflower','Golden sunflower')): ob.matrix_world=field_T@ob.matrix_world
# A cat on a tile ridge, exposed bricks, rain gutters and small foundations reward close inspection.
active=COL['details']
sphere('Ginger roof cat body',(-5.1,-3.4,2.02),(.09,.04,.055),WOOD)
sphere('Ginger roof cat head',(-5.0,-3.4,2.10),(.043,.035,.04),WOOD)
curve('Cat curled tail',[(-5.2,-3.4,2.02),(-5.26,-3.4,2.09),(-5.25,-3.35,2.15)],.016,WOOD,True)
for hx,hy in [(a,b*.72) for a,b in houses[:9]]:
    for j in range(random.randint(3,7)):
        box('Exposed old brick',(hx-.5+(j%3)*.13,hy-.65,.25+(j//3)*.06),(.12,.025,.055),ROOF,.006)
    if random.random()<.7: rod('Weathered rain downpipe',(hx+.61,hy-.62,.24),(hx+.61,hy-.62,1.26),.021,CONCRETE,8)
"""+mark)
# New road/field/yard masks for real particle flock.
s=s.replace("on_road=in_village and (abs(y)<1.2 or abs(abs(y)-5.04)<.55 or min(abs(x-a) for a in [-8,2,12])<.58)", "on_road=any((x-px)**2+(y-py)**2<.60**2 for path in new_paths for px,py,pz in path)")
s=s.replace("depot=-20<x<-10 and -5.8<y<-.2; field=-20.8<x<-13.7 and 5.2<y<9.3", "depot=-8.2<x<-.9 and 1.1<y<5.2; field=1.5<x<6.2 and -3.3<y<-.7")
s=s.replace("if in_village and (abs(y)<1.3 or abs(abs(y)-5.04)<.6 or min(abs(x-a) for a in [-8,2,12])<.65): continue", "if any((x-px)**2+(y-py)**2<.65**2 for path in new_paths for px,py,pz in path): continue")
s=s.replace("rigid=(-17,-1.33)","rigid=(-6.05,4.25)")
s=s.replace("rigid=(-3.35,2.63)","rigid=(-6.4,-.6)").replace("rigid=(-6.15,2.63)","rigid=(-5.1,-3.4)")
s=s.replace("'fallen_pole':(1.2,-.36,1.05),'meter':(-3.35,1.79,.86),'hot_roof':(-6.5,2.63,1.85),'depot':(-17,-1.9,1.2),'unsure_house':(4.55,2.63,1.8)","'fallen_pole':(1.2,-.36,1.05),'meter':(-6.4,-1.35,.86),'hot_roof':(-5.44,-3.4,1.85),'depot':(-6.05,4.05,1.1),'unsure_house':(6.3,.4,1.8)")
s=s.replace("'meter':(-3.35,2.63),'hot_roof':(-6.15,2.63),'depot':(-17,-1.33),'unsure_house':(4.55,2.63)","'meter':(-6.4,-.6),'hot_roof':(-5.1,-3.4),'depot':(-6.05,4.25),'unsure_house':(6.3,.4)")
# The flat map gets the actual new organic street curves.
a=s.index("for yy,w in [(0,.014)"); b=s.index('# Navy camera background',a)
s=s[:a]+"""for path in new_paths:
    strip_path('Cyan map road',[(x*S,y*S,.002) for x,y,z in path],.014,CYAN)
for i,(x,y) in enumerate([(-6.4,-.6),(-5.1,-3.4),(6.3,.4),(-6.05,4.25)]): sphere('Flat map anchor pin',(x*S,y*S,.008),(.008,.008,.005),[PPC,CYAN,ELECTRIC,PPC][i%4])
"""+s[b:]
p.write_text(s)
p=Path(__file__).resolve().with_name('render_planet.py'); s=p.read_text()
s=s.replace("(-1.9,-2.95,1.85)","(-.48,-2.08,1.16)").replace("(-1.3,-3.2,1.65)","(-.52,-2.02,1.03)").replace("(-1.55,-3.05,1.9)","(-.35,-2.1,1.18)")
s=s.replace("(-.62,-1.72,1.0)","(-.18,-1.05,.65)").replace("(-.02,-.01,.22)","(-.01,-.02,.14)")
s=s.replace("(.50,.48,.34)","(.30,.32,.23)")
s=s.replace("focus.location=(-.09,-.30,.28)","focus.location=(-.06,-.25,.13)").replace("focus.location=(-.12,-.31,.25)","focus.location=(-.06,-.25,.14)")
s=s.replace("focus.location=(-.13,-.29,.27)","focus.location=(-.15,-.22,.10)").replace("focus.location=(-.13,-.31,.26)","focus.location=(-.07,-.25,.15)")
p.write_text(s)
