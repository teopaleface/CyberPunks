from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

p = Path(__file__).resolve().parent
positions = [(2100,250),(2550,1050),(2700,650),(2350,600),(2400,350),(2400,800),(1200,800),(900,650),(1900,1400),(2400,900)]
files = sorted((p/'raw').glob('*.png'))
for i, src in enumerate(files):
    raw = Image.open(src).convert('RGB')
    # Requested fallback: 2x Lanczos followed by conforming to the required 4K frame.
    lanc = raw.resize((raw.width*2, raw.height*2), Image.Resampling.LANCZOS)
    lanc = ImageOps.fit(lanc, (3840,2160), method=Image.Resampling.LANCZOS)
    lanc.save(p/'qa'/f'{src.stem}_lanczos4k.png')
    esr = ImageOps.fit(Image.open(p/'qa'/f'{src.stem}_esrgan4x.png').convert('RGB'), (3840,2160), method=Image.Resampling.LANCZOS)
    esr.save(p/'qa'/f'{src.stem}_esrgan4k.png')
    x,y=positions[i]
    if i%4==0:
        sheet=Image.new('RGB',(1300,440*min(4,len(files)-i)),'#000F1E')
        d=ImageDraw.Draw(sheet)
    row=i%4
    for col,im in enumerate([lanc,esr]):
        d.text((col*650+10,row*440+8),f'{src.stem}: '+['Lanczos','Real-ESRGAN'][col],fill='white')
        sheet.paste(im.crop((x,y,x+650,y+400)),(col*650,row*440+30))
    if i%4==3 or i==len(files)-1:
        sheet.save(p/'qa'/f'upscale_comparison_{i//4+1}.jpg',quality=96)
print('Comparison sheets written')
