"""Conform selected enlargements, remove navy mattes, and build delivery sheets."""
from pathlib import Path
import json
import shutil
import numpy as np
from scipy import ndimage
from PIL import Image, ImageOps, ImageDraw, ImageFilter

p = Path(__file__).resolve().parent
CUTS = ['p01_storm','p02_dark','p04_wide','p06_unfold','p11_dawn','p12_day']

def extract(src, dst):
    image = Image.open(src).convert('RGB')
    rgb = np.asarray(image).astype(np.float32)
    h,w,_ = rgb.shape
    # Float distances avoid int16 overflow in squared RGB distances.
    border = np.concatenate([rgb[:4].reshape(-1,3),rgb[-4:].reshape(-1,3),rgb[:,:4].reshape(-1,3),rgb[:,-4:].reshape(-1,3)])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(rgb-bg,axis=2)
    navy = (rgb[:,:,2]>rgb[:,:,0]+5)&(rgb[:,:,2]>rgb[:,:,1]+3)&(rgb[:,:,0]<20)&(rgb[:,:,1]<35)&(rgb[:,:,2]<60)
    near = (dist<18)|navy
    labels,n = ndimage.label(near)
    counts=np.bincount(labels.ravel())
    exterior = np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]))
    exterior = exterior[exterior!=0]
    # Remove large enclosed navy pockets between wires; retain small dark details.
    close_counts=np.bincount(labels.ravel(),weights=(dist<12).ravel(),minlength=len(counts))
    if src.stem!='p01_storm':
        # Deep neutral truck windows at dawn must not be mistaken for navy void.
        large = np.flatnonzero((counts>1000)&(close_counts/np.maximum(counts,1)>.8))
    else:
        large = np.flatnonzero(counts>1000)
    large=large[large!=0]
    outside=np.isin(labels,np.union1d(exterior,large))
    mask=~outside
    # The generated navy forms small closed slivers between power wires.
    # Trim only blue matte at the exterior boundary, preserving dark earth inside.
    fringe=mask & ~ndimage.binary_erosion(mask,iterations=3)
    blue_matte=(rgb[:,:,2]>rgb[:,:,0]+5)&(rgb[:,:,2]>rgb[:,:,1]+3)&(rgb[:,:,0]<30)&(rgb[:,:,1]<45)&(rgb[:,:,2]<70)
    mask[fringe & blue_matte]=False
    if src.stem=='p01_storm':
        # The cloud's baked-in dark navy fringe needs a wider local trim.
        cloud=np.zeros(mask.shape,dtype=bool)
        cloud[:600,3000:]=True
        cloud_edge=mask & ~ndimage.binary_erosion(mask,iterations=10)
        mask[cloud & cloud_edge & (rgb.max(axis=2)<50)]=False
    # Remove isolated matte specks without removing the thin wires joined to poles.
    fg_labels,num=ndimage.label(mask)
    fg_counts=np.bincount(fg_labels.ravel())
    mask &= ~np.isin(fg_labels,np.flatnonzero(fg_counts<12))
    alpha=np.asarray(Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.55))).astype(np.float32)/255
    # Resolve edge pixels against nearby opaque colour, removing the navy fringe.
    core=ndimage.binary_erosion(mask,iterations=2)
    _,indices=ndimage.distance_transform_edt(~core,return_indices=True)
    nearest=rgb[indices[0],indices[1]]
    edge=(alpha>0)&(alpha<1)
    rgb[edge]=nearest[edge]
    rgb[alpha==0]=0
    rgba=np.dstack([np.clip(rgb,0,255).astype('uint8'),np.rint(alpha*255).astype('uint8')])
    result=Image.fromarray(rgba)
    result.save(dst)
    orange=Image.new('RGBA',result.size,'#FA4616')
    orange.alpha_composite(result)
    orange.convert('RGB').save(p/'qa'/f'{src.stem}_on_orange.jpg',quality=95)
    return dict(background=bg.tolist(),opaque_fraction=float((alpha>.99).mean()),transparent_fraction=float((alpha==0).mean()))

def sheet(files,dest,columns=2,width=800):
    height=width*9//16
    gap=16; label=32
    rows=(len(files)+columns-1)//columns
    out=Image.new('RGB',(columns*width+(columns+1)*gap,rows*(height+label)+(rows+1)*gap),'#000F1E')
    draw=ImageDraw.Draw(out)
    for i,f in enumerate(files):
        x=gap+(i%columns)*(width+gap); y=gap+(i//columns)*(height+label+gap)
        draw.text((x+4,y+7),f.stem.replace('_on_orange',''),fill='white')
        im=ImageOps.fit(Image.open(f).convert('RGB'),(width,height),method=Image.Resampling.LANCZOS)
        out.paste(im,(x,y+label))
    out.save(dest,quality=96)

if __name__=='__main__':
    choices=json.loads((p/'upscale_selection.json').read_text())
    for name,method in choices.items():
        shutil.copyfile(p/'qa'/f'{name}_{method}4k.png',p/'up'/f'{name}.png')
    metrics={}
    for name in CUTS:
        metrics[name]=extract(p/'up'/f'{name}.png',p/'cut'/f'{name}.png')
        print(name,'cut',flush=True)
    (p/'qa'/'cutout_metrics.json').write_text(json.dumps(metrics,indent=2))
    sheet(sorted((p/'up').glob('*.png')),p/'contact.jpg')
    sheet([p/'qa'/f'{name}_on_orange.jpg' for name in CUTS],p/'qa'/'cutout_orange_contact.jpg')
    print('Delivery sheets written')
