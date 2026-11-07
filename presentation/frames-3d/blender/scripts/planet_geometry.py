"""Native Geometry Nodes for exact azimuthal flat-to-planet rolling, shared by every mesh and anchor."""
import bpy,math
from mathutils import Vector

def azimuthal(p,radius,factor=1):
    x,y,h=p; r=math.hypot(x,y)
    if factor<1e-6 or r<1e-9: return Vector((x,y,radius+h))
    a=factor*r/radius; rr=radius/factor
    normal=Vector((math.sin(a)*x/r,math.sin(a)*y/r,math.cos(a)))
    surface=Vector((rr*math.sin(a)*x/r,rr*math.sin(a)*y/r,radius+rr*(math.cos(a)-1)))
    return surface+normal*h

def azimuthal_rigid(p,center,radius,factor=1):
    cx,cy=center; rr=math.hypot(cx,cy)
    if factor<1e-6 or rr<1e-9: return Vector((p.x,p.y,radius+p.z))
    a=factor*rr/radius; ux,uy=cx/rr,cy/rr; co,si=math.cos(a),math.sin(a)
    base=azimuthal((cx,cy,0),radius,factor); dx,dy,h=p.x-cx,p.y-cy,p.z
    ex=Vector((co+uy*uy*(1-co),-ux*uy*(1-co),-ux*si))
    ey=Vector((-ux*uy*(1-co),co+ux*ux*(1-co),-uy*si)); normal=Vector((ux*si,uy*si,co))
    return base+ex*dx+ey*dy+normal*h

def make_roll_group(radius):
    group=bpy.data.node_groups.new('Daybreak | exact rolling sphere','GeometryNodeTree'); group.is_modifier=True
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    factor=group.interface.new_socket(name='Roll factor',in_out='INPUT',socket_type='NodeSocketFloat'); factor.default_value=1; factor.min_value=0; factor.max_value=1
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    N=group.nodes; L=group.links
    inp=N.new('NodeGroupInput'); out=N.new('NodeGroupOutput')
    def connect(value,socket):
        if hasattr(value,'is_output'): L.new(value,socket)
        else: socket.default_value=value
    def mathnode(op,a,b=None):
        node=N.new('ShaderNodeMath'); node.operation=op; connect(a,node.inputs[0])
        if b is not None: connect(b,node.inputs[1])
        return node.outputs[0]
    def vecnode(op,a,b=None,scale=None):
        node=N.new('ShaderNodeVectorMath'); node.operation=op; connect(a,node.inputs[0])
        if b is not None: connect(b,node.inputs[1])
        if scale is not None: connect(scale,node.inputs[3])
        return node.outputs['Value'] if op in ['LENGTH','DOT_PRODUCT','DISTANCE'] else node.outputs['Vector']
    def split(v):
        node=N.new('ShaderNodeSeparateXYZ'); connect(v,node.inputs[0]); return tuple(node.outputs)
    def comb(x,y,z):
        node=N.new('ShaderNodeCombineXYZ')
        for value,socket in zip([x,y,z],node.inputs): connect(value,socket)
        return node.outputs[0]
    def switch(flag,a,b):
        node=N.new('GeometryNodeSwitch'); node.input_type='VECTOR'; connect(flag,node.inputs['Switch']); connect(a,node.inputs['False']); connect(b,node.inputs['True']); return node.outputs[0]
    attr=N.new('GeometryNodeInputNamedAttribute'); attr.data_type='FLOAT_VECTOR'; attr.inputs['Name'].default_value='flat_position'; flat=attr.outputs['Attribute']; fx,fy,fz=split(flat)
    ac=N.new('GeometryNodeInputNamedAttribute'); ac.data_type='FLOAT_VECTOR'; ac.inputs['Name'].default_value='actor_center'; cx,cy,rigid=split(ac.outputs['Attribute'])
    use_rigid=mathnode('GREATER_THAN',rigid,.5)
    base=switch(use_rigid,comb(fx,fy,0),comb(cx,cy,0)); bx,by,_=split(base)
    dist=vecnode('LENGTH',base); safe=mathnode('MAXIMUM',dist,1e-8); ux=mathnode('DIVIDE',bx,safe); uy=mathnode('DIVIDE',by,safe)
    f=inp.outputs['Roll factor']; theta=mathnode('DIVIDE',mathnode('MULTIPLY',f,dist),radius); si=mathnode('SINE',theta); co=mathnode('COSINE',theta)
    bend_radius=mathnode('DIVIDE',radius,mathnode('MAXIMUM',f,1e-6)); tangent=mathnode('MULTIPLY',bend_radius,si)
    curved=comb(mathnode('MULTIPLY',ux,tangent),mathnode('MULTIPLY',uy,tangent),mathnode('ADD',radius,mathnode('MULTIPLY',bend_radius,mathnode('SUBTRACT',co,1))))
    zero=mathnode('LESS_THAN',f,.0001); surface=switch(zero,curved,comb(bx,by,radius))
    normal=comb(mathnode('MULTIPLY',ux,si),mathnode('MULTIPLY',uy,si),co)
    height=mathnode('SUBTRACT',fz,radius); flexible=vecnode('ADD',surface,vecnode('SCALE',normal,scale=height))
    offset=vecnode('SUBTRACT',flat,comb(cx,cy,radius)); rotate=N.new('ShaderNodeVectorRotate'); rotate.rotation_type='AXIS_ANGLE'
    connect(offset,rotate.inputs['Vector']); connect(comb(mathnode('MULTIPLY',uy,-1),ux,1e-8),rotate.inputs['Axis']); connect(theta,rotate.inputs['Angle'])
    instance=vecnode('ADD',surface,rotate.outputs['Vector']); position=switch(use_rigid,flexible,instance)
    setpos=N.new('GeometryNodeSetPosition'); L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']); L.new(position,setpos.inputs['Position']); L.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    # A readable graph when the native project is opened.
    for i,node in enumerate(N): node.location=((i%8)*220,-(i//8)*180)
    return group,factor.identifier

def attach_roll(obj,group,identifier,control,flat,centers):
    attr=obj.data.attributes.new('flat_position','FLOAT_VECTOR','POINT'); attr.data.foreach_set('vector',[c for p in flat for c in p])
    attr=obj.data.attributes.new('actor_center','FLOAT_VECTOR','POINT'); attr.data.foreach_set('vector',[c for p in centers for c in p])
    mod=obj.modifiers.new('Planet roll | one animated factor','NODES'); mod.node_group=group
    socket=getattr(mod.properties.inputs,identifier); socket.value=1.
    driver=socket.driver_add('value').driver; driver.expression='factor'; v=driver.variables.new(); v.name='factor'; v.targets[0].id=control; v.targets[0].data_path='["flat_to_planet"]'
    return mod
