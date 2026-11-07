"""Additional authored miniature geometry; imported by build_objects.py."""
def extend(ns):
    globals().update(ns)
    def pole():
        concrete=mat('Pitted old cast concrete','#A19D8E',.91,0,.65,95)
        n=concrete.node_tree.nodes;co=n.new('ShaderNodeTexCoord');concrete.node_tree.links.new(co.outputs['Object'],n.get('Noise Texture').inputs['Vector'])
        brown=mat('Brown glazed ceramic','#633C27',.26,.05,.12,190)
        oxide=mat('Oxidised exposed reinforcing steel','#77503B',.88,.45,.3)
        zinc=mat('Weathered galvanised crossarm','#7D8785',.56,.72,.29,130)
        N=28;verts=[];zs=[-1.70,-1.52,-.6,.5,1.65]
        for k,z in enumerate(zs):
            for i in range(N):
                a=i*2*PI/N;r=(.245-k*.011)*(1+random.uniform(-.035,.035))
                zz=z+(random.uniform(-.07,.07) if k==0 else random.uniform(-.012,.012))
                verts.append((r*math.cos(a),r*math.sin(a),zz))
        faces=[tuple(range(N-1,-1,-1)),tuple((len(zs)-1)*N+i for i in range(N))]
        for k in range(len(zs)-1):
            for i in range(N):faces.append((k*N+i,k*N+(i+1)%N,(k+1)*N+(i+1)%N,(k+1)*N+i))
        o=mesh('Fractured cast-concrete pole fragment',verts,faces,concrete);smooth(o)
        # Crossarm, saddle and two strain insulators.
        box('Galvanised steel crossarm',(0,0,1.08),(2.58,.22,.18),zinc,.018)
        for z in [.80,1.27]:
            torus('Pole clamp band',(0,0,z),.225,.024,zinc)
            screw((0,-.252,z),r=.042)
        for x in [-1.02,1.02]:
            rod('Diagonal arm support',(0,.03,.48),(x,.03,1.02),.028,zinc)
            rod('Insulator metal spindle',(x,0,1.13),(x,0,1.65),.035,STEEL)
            # A turned ceramic stack with three umbrella skirts.
            cyl('Ceramic insulator neck',(x,0,1.47),.11,.51,brown)
            for z,r in [(1.30,.21),(1.43,.19),(1.56,.16)]:
                bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r,radius2=r*.60,depth=.092,location=(x,0,z));o=bpy.context.object;o.name='Glazed ceramic rain skirt';assign(o,brown);smooth(o);bevel(o,.016)
            torus('Conductor saddle',(x,0,1.72),.081,.023,brown)
            curve('Broken stranded overhead conductor',[(x-.12,-.025,1.72),(x+.18,-.015,1.75),(x+.46,-.03,1.58),(x+.67,-.04,1.23)],.024,BLACK)
            for j in range(5):
                curve('Frayed conductor strand',[(x+.57,-.04,1.43),(x+.68+random.uniform(-.10,.13),random.uniform(-.08,.07),1.18+random.uniform(-.12,.09))],.0045,STEEL)
        # Rough aggregate at the jagged fracture and bent reinforcing bar.
        for i in range(36):
            a=random.uniform(0,2*PI);rr=random.uniform(.02,.22)
            uv('Exposed fracture aggregate',(rr*math.cos(a),rr*math.sin(a),random.uniform(-1.78,-1.61)),(random.uniform(.018,.045),random.uniform(.018,.04),random.uniform(.02,.065)),mat('Concrete aggregate '+str(i),'#6E7067',.95,0,.2),12,6)
        for a in [0,2.1,4.2]:
            x=.14*math.cos(a);y=.14*math.sin(a)
            curve('Bent fractured reinforcing bar',[(x,y,-1.50),(x,y,-1.83),(x+.07,y-.035,-2.07)],.016,oxide)
            for j in range(7):torus('Rebar transverse rib',(x,y,-1.55-j*.045),.017,.0035,oxide,segs=16)
        for i in range(4):
            x=random.uniform(-.12,.12);z=random.uniform(-1.3,.9)
            curve('Concrete hairline crack',[(x,-.23,z),(x+.025,-.232,z+.07),(x+.01,-.234,z+.12)],.0008,DARK)
    def solar():
        frame=mat('Brushed anodised aluminium','#A8B3B5',.36,.85,.15,270)
        back=mat('Dusty offwhite solar backsheet','#B6B9B1',.77,0,.25)
        box('Panel backsheet',(0,0,0),(2.28,3.47,.085),back,.012)
        box('Dark perimeter seal',(0,0,.05),(2.25,3.44,.025),RUBBER,.008)
        for x in [-1.18,1.18]:box('Extruded side frame',(x,0,.035),(.078,3.62,.16),frame,.012)
        for y in [-1.77,1.77]:box('Extruded end frame',(0,y,.035),(2.40,.078,.16),frame,.012)
        cells=[mat('Blue silicon cell batch '+str(i),c,.28,.46,.09,260) for i,c in enumerate(['#142E4C','#18334E','#203C55','#162D47'])]
        fine=mat('Etched silver conductive traces','#647783',.48,.62,.1)
        verts=[];faces=[]
        for ix in range(6):
            for iy in range(10):
                x=(ix-2.5)*.365;y=(iy-4.5)*.337;w=.345;h=.315;c=.026;z=.075
                points=[(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]
                mesh('Chamfered photovoltaic wafer',[(x+xx,y+yy,z) for xx,yy in points],[tuple(range(8))],random.choice(cells))
                for xx in [-.095,0,.095]:
                    k=len(verts);verts.extend([(x+xx-.0025,y-h/2,z+.002),(x+xx+.0025,y-h/2,z+.002),(x+xx+.0025,y+h/2,z+.002),(x+xx-.0025,y+h/2,z+.002)]);faces.append(tuple(range(k,k+4)))
                for j in range(15):
                    yy=y-h/2+(j+.5)*h/15;k=len(verts);verts.extend([(x-w/2,yy-.0007,z+.002),(x+w/2,yy-.0007,z+.002),(x+w/2,yy+.0007,z+.002),(x-w/2,yy+.0007,z+.002)]);faces.append(tuple(range(k,k+4)))
        mesh('Fine screenprinted cell conductors',verts,faces,fine)
        # A very thin clear encapsulant, low IOR, no toy gloss.
        glass=mat('Dusty panel encapsulant','#66819A',.28,.05,.015,120)
        glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.92
        glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.44
        # Cell coating is in the wafer shader so the delicate grid remains legible.
        for m in cells:m.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.18
        for y in [-1.10,1.10]:
            box('Rear mounting rail',(0,y,-.125),(2.28,.085,.11),frame,.009)
            for x in [-1.08,1.08]:screw((x,y,.124),'Z',.023)
        box('Rear junction box',(0,.67,-.116),(.54,.57,.16),BLACK,.035)
        for x in [-.16,.16]:
            curve('Solar output lead',[(x,.65,-.19),(x*2,.14,-.23),(x*3,-.32,-.18)],.016,RUBBER)
            cyl('Solar cable connector',(x*3,-.32,-.18),.033,.15,BLACK,'Y')
        for i in range(90):
            x=random.uniform(-1.08,1.08);y=random.uniform(-1.66,1.66)
            uv('Fine settled dust speck',(x,y,.092),(.003,.004,.001),MUD,8,4)
    def hardhat():
        orange=mat('Scuffed PPC orange safety helmet','#FA4616',.46,0,.12,210)
        inner=mat('Moulded helmet interior','#B53915',.65,0,.12)
        scuff=mat('Faint abraded orange paint','#D98249',.83,0,.18)
        N=96;R=24;v=[];f=[]
        for j in range(R+1):
            th=.018+(1.48-.018)*j/R
            for i in range(N):
                a=i*2*PI/N;v.append((1.02*math.sin(th)*math.cos(a),.91*math.sin(th)*math.sin(a),1.08*math.cos(th)))
        for j in range(R):
            for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
        f.append(tuple(range(N-1,-1,-1)))
        o=mesh('Thin moulded helmet dome',v,f,orange);smooth(o);sol=o.modifiers.new('Real shell wall thickness','SOLIDIFY');sol.thickness=.037;sol.offset=-1
        # Annular flared brim, extended peak over the front.
        v=[];f=[]
        for j in range(4):
            t=j/3
            for i in range(N):
                a=i*2*PI/N;front=max(0,-math.sin(a));x=(1.015+.15*t)*math.cos(a);y=(.905+.12*t+.15*t*front**4)*math.sin(a);z=.097-.07*t+.025*math.cos(a*2)
                v.append((x,y,z))
        for j in range(3):
            for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
        o=mesh('Flared brim and front visor',v,f,orange);smooth(o);sol=o.modifiers.new('Brim thickness','SOLIDIFY');sol.thickness=.035;bevel(o,.012)
        # Three raised moulding ribs follow the shell.
        for x in [-.34,0,.34]:
            pts=[]
            for k in range(25):
                y=-.79+1.58*k/24;z=1.08*math.sqrt(max(.01,1-(x/1.02)**2-(y/.91)**2))+.015;pts.append((x,y,z))
            curve('Raised impact reinforcing rib',pts,.024 if x else .032,orange)
        for x in [-1,1]:
            box('Accessory slot',(x*.986,.08,.18),(.039,.24,.08),DARK,.014)
            box('Slot reinforced edge',(x*1.005,.08,.17),(.03,.27,.025),orange,.009)
        # Readable interior in the back half of the spin.
        torus('Interior headband',(0,0,.08),.73,.037,RUBBER)
        for a in [0,PI/2,PI,3*PI/2]:
            pts=[(.74*math.cos(a),.74*math.sin(a),.09),(.42*math.cos(a),.42*math.sin(a),.70),(0,0,.93)]
            curve('Interior suspension strap',pts,.035,inner)
        for i in range(48):
            a=random.uniform(0,2*PI);th=random.uniform(.45,1.42);x=1.024*math.sin(th)*math.cos(a);y=.914*math.sin(th)*math.sin(a);z=1.084*math.cos(th)
            curve('Short rubbed shell scuff',[(x,y,z),(x+.018*math.cos(a+.8),y+.018*math.sin(a+.8),z+.009)],random.uniform(.0008,.002),scuff)
    def pin(color):
        head=mat('PPC pin lacquer '+color,color,.26,.05,.055,300)
        uv('Round lacquered map pin head',(0,0,.60),(.41,.41,.41),head,64,32)
        cyl('Steel pin collar',(0,0,.21),.065,.16,STEEL)
        cyl('Fine steel needle',(0,0,-.36),.026,1.03,STEEL,verts=32)
        bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=0,radius2=.026,depth=.18,location=(0,0,-.965));o=bpy.context.object;o.name='Sharp steel needle point';assign(o,STEEL);smooth(o)
    def cloud():
        cotton=mat('Carded grey wool with soft fibre scatter','#7A8283',.98,0,.20,160)
        p=cotton.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.65;p.inputs['Subsurface Weight'].default_value=.22;p.inputs['Subsurface Radius'].default_value=(.1,.1,.1)
        fibre=mat('Individual cool grey wool fibres','#9CA4A1',.98,0,.05,260)
        # Overlapping asymmetrical clumps remeshed into a continuous hand-teased shape.
        clumps=[]
        for x,y,z,sx,sy,sz in [(-1.25,0,0,.75,.59,.47),(-.5,-.04,.17,.86,.65,.61),(.35,.02,.18,.95,.68,.61),(1.1,.04,.02,.82,.58,.49),(-.63,.04,.62,.61,.51,.49),(.1,.1,.77,.65,.50,.5),(.78,.12,.59,.64,.53,.49),(-1.6,-.04,-.03,.44,.40,.32),(1.65,-.01,-.08,.45,.40,.33),(-.2,-.3,-.2,1.04,.45,.35)]:
            clumps.append(uv('Teased wool mass',(x,y,z),(sx,sy,sz),cotton,32,20))
        bpy.ops.object.select_all(action='DESELECT')
        for o in clumps:o.select_set(True)
        bpy.context.view_layer.objects.active=clumps[0];bpy.ops.object.join();o=clumps[0]
        mod=o.modifiers.new('Unify cotton masses','REMESH');mod.mode='VOXEL';mod.voxel_size=.055;bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=o.modifiers.new('Soften hand-teased joins','SMOOTH');mod.factor=1.1;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)
        tex=bpy.data.textures.new('Coarse irregular cotton fibres',type='CLOUDS');tex.noise_scale=.16;tex.noise_depth=2
        mod=o.modifiers.new('Uneven pulled wool surface','DISPLACE');mod.texture=tex;mod.strength=.14;mod.texture_coords='GLOBAL';bpy.ops.object.modifier_apply(modifier=mod.name);smooth(o)
        # True curves along the actual surface normals, not a painted alpha card.
        d=bpy.data.curves.new('Tens of thousands of teased wool filaments','CURVE');d.dimensions='3D';d.resolution_u=1;d.bevel_depth=.00085;d.bevel_resolution=0;d.resolution_u=1
        polys=list(o.data.polygons)
        for i in range(42000):
            face=random.choice(polys);ids=list(face.vertices);vs=[o.data.vertices[k] for k in ids]
            u=random.random();vv=random.random();a=vs[0].co.lerp(vs[1].co,u).lerp(vs[-1].co,vv)
            a=o.matrix_world@a;n=(o.matrix_world.to_3x3()@face.normal).normalized()
            tangent=n.cross(Vector((.32,.79,.27))).normalized();bit=n.cross(tangent)
            length=random.uniform(.035,.24);phase=random.uniform(0,2*PI);curl=random.uniform(.015,.070);freq=random.uniform(2.6,5.6)
            points=[]
            for k in range(7):
                t=k/6;angle=phase+t*freq
                co=a+n*(math.sin(t*PI)*length*.45-.007)+tangent*(math.sin(angle)-math.sin(phase))*curl+bit*(math.cos(angle)-math.cos(phase))*curl
                points.append(co)
            sp=d.splines.new('BEZIER');sp.bezier_points.add(6);sp.resolution_u=2
            thick=random.uniform(.4,1)
            for k,(pt,co) in enumerate(zip(sp.bezier_points,points)):
                pt.co=co;pt.handle_left_type='AUTO';pt.handle_right_type='AUTO';pt.radius=thick*(.2+.8*math.sin(PI*(k+.5)/7))
        obj=bpy.data.objects.new('Visible cotton-wool fibre halo',d);bpy.context.collection.objects.link(obj);assign(obj,fibre)
    ns['BUILDERS'].update(pole=pole,solar=solar,hardhat=hardhat,pin_orange=lambda:pin('#FA4616'),pin_cyan=lambda:pin('#00A3E0'),pin_blue=lambda:pin('#163FE8'),cloud=cloud)
