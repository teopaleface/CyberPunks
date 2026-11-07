import bpy, json
p=bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type='METAL'
p.get_devices()
print('OBJECTS_DEVICES', [(d.name,d.type) for d in p.devices])
