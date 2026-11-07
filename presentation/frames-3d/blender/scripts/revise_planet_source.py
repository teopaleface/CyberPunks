from pathlib import Path
p=Path(__file__).resolve().with_name('build_planet.py'); s=p.read_text()
s=s.replace("mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=tint_mix", "mix.blend_type='MIX'; mix.inputs[0].default_value=tint_mix")
s=s.replace("1.3,'EEE8DD',.18,.28", "1.3,'EEE8DD',.88,.28")
s=s.replace("'clay_roof_tiles_02',1.4,None,0,.65", "'clay_roof_tiles_02',1.4,'B5523A',.28,.65")
# Add larger, irregular focal walnut trees to break the repeated house rows.
mark='# Real leaf cards replace the faceted crown balls.'
s=s.replace(mark,"""# Large old walnut trees form the visual hierarchy of a real village model.
active=COL['village']
for x,y,sc in [(-10.4,2.4,1.28),(-10.4,5.6,1.15),(-.3,1.7,1.15),(6.7,-5.7,1.08),(8.3,6.7,1.2)]: tree(x,y,sc)
trunk_centers=[(o.matrix_world.translation.x,o.matrix_world.translation.y) for o in COL['village'].objects if o.name.startswith('Walnut trunk')]
"""+mark)
# Old matrix updates are essential after adding parents and transformed details.
s=s.replace("active=COL['foliage']; lv=[]; lf=[]", "bpy.context.view_layer.update()\nactive=COL['foliage']; lv=[]; lf=[]; leaf_attach=[]")
s=s.replace("center=o.matrix_world.translation; scales=Vector(o.scale)", "center=o.matrix_world.translation; scales=Vector(o.scale)*1.22\n    attachment=min(trunk_centers,key=lambda p:(p[0]-center.x)**2+(p[1]-center.y)**2)")
s=s.replace("        idx=len(lv); lv.extend", "        leaf_attach.extend([attachment]*5)\n        idx=len(lv); lv.extend")
# Replace coarse box roads with finely divided quads that follow the sphere.
a=s.index("for yy,ww in [(0,2.25)"); b=s.index('# The depot is now',a)
s=s[:a]+"""def road_strip(name,axis,center,length,width,material):
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
for yy,ww in [(0,2.25),(-5.04,.94),(5.04,.94)]: road_strip('Worn asphalt rural road','X',yy,43.4,ww,ASPHALT)
for xx in [-8,2,12]: road_strip('Gravel side lane','Y',xx,19.,1.0,GRAVEL)
"""+s[b:]
# Resample the tape along every straight section before spherical wrapping.
s=s.replace("    vs=[]; fs=[]; width=.27", "    dense=[pts[0]]\n    for aa,bb in zip(pts,pts[1:]):\n        count=max(1,math.ceil((bb-aa).length/.16))\n        dense.extend(aa.lerp(bb,j/count) for j in range(1,count+1))\n    pts=dense\n    vs=[]; fs=[]; width=.38")
# Store attachment centres in the combined evaluated meshes. They preserve whole buildings.
s=s.replace("'density':density if o==terrain else None", "'density':density if o==terrain else None,'centers':[]")
s=s.replace("        b['v'].extend([tuple(mw@v) for v in local])", """        coords=[mw@v for v in local]
        root=o
        while root.parent is not None: root=root.parent
        rigid=None; n=o.name.lower(); center=mw.translation
        if root.type=='EMPTY' and root.name!='Actual hot-roof panel assembly': rigid=(root.location.x,root.location.y)
        elif 'depot' in n or 'workshop' in n or 'stored repair' in n: rigid=(-17,-1.33)
        elif o==cloud_obj or any(k in n for k in ['rain','cloud','filament','fishing-line']): rigid=(7,1.44)
        elif any(k in n for k in ['snapped concrete','broken pole','fallen crossarm','loose fallen']): rigid=(2.4,.5)
        elif 'walnut trunk' in n: rigid=(center.x,center.y)
        elif 'dog' in n: rigid=(-16.8,-4.8)
        elif 'laundry' in n: rigid=(-3.4,3.8)
        elif 'meter' in n or 'tampering' in n: rigid=(-3.35,2.63)
        elif root.name=='Actual hot-roof panel assembly': rigid=(-6.15,2.63)
        elif cname=='village' and not any(k in n for k in ['sunflower','road','lane','barrel roof tiles']):
            cc=sum(coords,Vector())/len(coords)
            near=min(flat_houses,key=lambda q:(q[0]-cc.x)**2+(q[1]-cc.y)**2)
            if (near[0]-cc.x)**2+(near[1]-cc.y)**2<4: rigid=near
        if o.name=='Translucent individual walnut leaf clusters': centers=leaf_attach
        elif 'barrel roof tiles' in n: centers=[min(flat_houses,key=lambda q:(q[0]-v.x)**2+(q[1]-v.y)**2) for v in coords]
        else: centers=[rigid]*len(coords)
        b['v'].extend([tuple(v) for v in coords]); b['centers'].extend(centers)""")
s=s.replace("def sphere_point(p):", """def rigid_point(p,center):
    cx,cy=center; lon=cx/R; lat=cy/R+LAT
    n=Vector((math.cos(lat)*math.sin(lon),-math.cos(lat)*math.cos(lon),math.sin(lat)))
    ex=Vector((math.cos(lon),math.sin(lon),0)); ey=Vector((-math.sin(lat)*math.sin(lon),math.sin(lat)*math.cos(lon),math.cos(lat)))
    return n*(R+p.z)+ex*(p.x-cx)+ey*(p.y-cy)
def sphere_point(p):""")
s=s.replace("flat=[warp(v)*S for v in b['v']]; sph=[sphere_point(warp(v))*S for v in b['v']]", """points=[]; sph=[]
    for v,center in zip(b['v'],b['centers']):
        pp=warp(v)
        if center is not None:
            pp.z-=.10; cc=warp((*center,0)); qq=rigid_point(pp,(cc.x,cc.y))
        else: qq=sphere_point(pp)
        points.append(pp*S); sph.append(qq*S)
    flat=points""")
s=s.replace("42000,.0024,HAIR,3", "240000,.0026,HAIR,5")
s=s.replace("settings.roughness_1=.025; settings.roughness_2=.012", "settings.roughness_1=.0004; settings.roughness_2=.0002")
s=s.replace("navy.inputs['Strength'].default_value=1", "navy.inputs['Strength'].default_value=3")
s=s.replace("f=warp(p0)*S; q=sphere_point(warp(p0))*S", """pp=warp(p0); pp.z-=.1; f=pp*S
    centers={'fallen_pole':(2.4,.5),'meter':(-3.35,2.63),'hot_roof':(-6.15,2.63),'depot':(-17,-1.33),'unsure_house':(4.55,2.63)}
    cc=warp((*centers.get(name,(p0[0],p0[1])),0)); q=rigid_point(pp,(cc.x,cc.y))*S""")
s=s.replace("'hairs':42000,'children_per_parent':3", "'hairs':240000,'children_per_parent':5")
s=s.replace("Every evaluated vertex: lerp(original flat metres, equirectangular spherical metres)", "Shared lerp of flat and sphere; buildings and vehicles use rigid radial tangent frames; ground/roads use per-vertex wrapping")
p.write_text(s)
