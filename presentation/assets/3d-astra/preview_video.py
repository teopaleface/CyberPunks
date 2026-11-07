"""White-background video preview from the exact delivered PNG frames; no audio."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
NAMES=['meter','transformer','solar','storm','helmet']
LABELS=['Contor inteligent','Transformator','Panou solar','Furtună','Cască de protecție']
try: font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',25)
except OSError: font=ImageFont.load_default(size=25)
frames=[]
for f in range(30):
    out=Image.new('RGB',(1600,364),'white'); draw=ImageDraw.Draw(out)
    for i,(name,label) in enumerate(zip(NAMES,LABELS)):
        im=Image.open(HERE/(name+'_spin')/f'{f:04d}.png').resize((320,320),Image.Resampling.LANCZOS)
        out.paste(im,(320*i,0),im); draw.text((320*i+160,341),label,font=font,fill='#0B1622',anchor='mm')
    frames.append(out.tobytes())
cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x364','-framerate','30','-i','-','-an','-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'turntables_white.mp4')]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for _ in range(2):
    for frame in frames: proc.stdin.write(frame)
    for _ in range(30): proc.stdin.write(frames[-1])
proc.stdin.close(); assert proc.wait()==0
print(HERE/'turntables_white.mp4')
