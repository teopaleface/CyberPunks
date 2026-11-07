import bpy
p=bpy.context.preferences.addons['cycles'].preferences
print('CYCLES_METAL_OPTIONS',[(a.identifier,getattr(p,a.identifier)) for a in p.bl_rna.properties if any(x in a.identifier for x in ['metal','kernel','device']) and a.identifier!='devices'])
s=bpy.context.scene
print('CYCLES_BLUR_OPTIONS',[(a.identifier,getattr(s.cycles,a.identifier)) for a in s.cycles.bl_rna.properties if 'motion_blur' in a.identifier or 'denoising_use_gpu' in a.identifier])
