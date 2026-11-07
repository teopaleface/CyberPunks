from pathlib import Path
import subprocess, time
p=Path(__file__).resolve().parent
for src in sorted((p/'raw').glob('*.png')):
 out=p/'qa'/f'{src.stem}_esrgan4x.png'
 if out.exists(): continue
 start=time.time()
 with (p/'qa'/f'upscale-{src.stem}.log').open('w') as log:
  r=subprocess.run(['/tmp/daybreak-realesrgan/realesrgan-ncnn-vulkan','-i',str(src),'-o',str(out),'-s','4','-n','realesrgan-x4plus','-m','/tmp/daybreak-realesrgan/models','-t','128'],stdout=log,stderr=log)
 print(src.stem, 'exit',r.returncode, 'seconds',round(time.time()-start,1),flush=True)
 if r.returncode: raise SystemExit(r.returncode)
