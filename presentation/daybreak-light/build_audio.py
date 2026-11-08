"""Keep the supplied mix's timing; update two lines using its original local voice."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly
import pyloudnorm as pyln

HERE = Path(__file__).resolve().parent
SOURCE = Path('/Users/teo/.t3/worktrees/CyberPunks/Teo-prezentare/presentation/frames-3d/audio')
OUT = HERE / 'assets/local'
OUT.mkdir(parents=True, exist_ok=True)
clock = json.loads((SOURCE / 'timing.json').read_text())
spec = importlib.util.spec_from_file_location('original_tts', SOURCE / 'tools/tts.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
engine = Kokoro('/tmp/kokoro-models/kokoro-v1.0.onnx', '/tmp/kokoro-models/voices-v1.0.bin')
voice, sr = sf.read(SOURCE / 'vo/vo_af_heart.wav', always_2d=True)
meter = pyln.Meter(sr)
updates = {
    4: 'Tomorrow, eleven crews must handle six hundred and eighty-nine problems.',
    9: 'and plans efficient routes for every crew.',
}
for index, text in updates.items():
    raw, raw_sr = engine.create(text, voice='af_heart', speed=0.93, lang='en-us')
    raw = mod.trim(np.asarray(raw, dtype=np.float32), raw_sr)
    line = clock['lines'][index - 1]
    old_file, old_sr = sf.read(SOURCE / line['file'])
    target = len(old_file) / old_sr
    source_file = OUT / f'line_{index:02d}_raw.wav'
    timed_file = OUT / f'line_{index:02d}.wav'
    sf.write(source_file, raw, raw_sr)
    tempo = len(raw) / raw_sr / target
    chain = f'atempo={tempo:.8f},highpass=f=75,equalizer=f=280:t=q:w=1.1:g=-1.5,equalizer=f=3200:t=q:w=1.3:g=1.5,highshelf=f=8500:g=1,acompressor=threshold=0.08:ratio=2.5:attack=4:release=120:knee=4,deesser=i=0.25:m=0.5:f=0.5,apad'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(source_file),'-af',chain,'-t',str(target),'-ar',str(sr),str(timed_file)],check=True)
    new, _ = sf.read(timed_file)
    a = round(line['file_start'] * sr)
    count = min(len(new), len(voice) - a)
    old = voice[a:a+count].mean(axis=1)
    gain = 10 ** ((meter.integrated_loudness(old) - meter.integrated_loudness(new[:count])) / 20)
    voice[a:a+count] = (new[:count] * gain)[:,None]
    sf.write(timed_file, new * gain, sr, subtype='PCM_24')
    line['text'] = text
    line['words'] = []
    print(index, text, 'tempo', round(tempo, 3), flush=True)

music, msr = sf.read(SOURCE / 'local/music_bed_ducked.wav', always_2d=True)
effects, esr = sf.read(SOURCE / 'sfx_stem.wav', always_2d=True)
assert msr == esr == sr
# Match the existing click to the new visual approval frame.
a, b = round(36.463*sr), round(36.763*sr)
click = effects[a:b].copy()
effects[a:b] = 0
dest = round(35.55*sr)
effects[dest:dest+len(click)] += click
n = min(len(voice),len(music),len(effects))
sf.write(OUT / 'mix_unmastered.wav', voice[:n]+music[:n]+effects[:n], sr, subtype='FLOAT')
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(OUT/'mix_unmastered.wav'),'-af','loudnorm=I=-14:TP=-1.3:LRA=7','-ar','48000','-c:a','aac','-b:a','256k',str(OUT/'mix.m4a')],check=True)
(HERE/'assets/timing.json').write_text(json.dumps(clock,ensure_ascii=False,indent=2))
