"""Verify the exact deliverables and pack the original RGBA turntable frames.

Requires Python 3, Pillow and NumPy. Optional FFmpeg produces a white-background
MP4 preview from the delivered frames. It never changes the source renders.
"""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

OUT = Path(__file__).resolve().parent
NAMES = ("meter", "transformer", "solar", "storm", "helmet")
LABELS = ("contor", "transformator", "panou solar", "furtună", "cască")
parser = argparse.ArgumentParser()
parser.add_argument("--heroes-only", action="store_true")
parser.add_argument("--video", action="store_true")
args = parser.parse_args()


def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def on_white(im):
    bg = Image.new("RGBA", im.size, "white")
    return Image.alpha_composite(bg, im).convert("RGB")


def check(path, size):
    assert path.exists(), str(path)+" is missing"
    with Image.open(path) as im:
        im.load()
        assert im.size == size, (str(path), im.size, size)
        assert im.mode == "RGBA", (str(path), im.mode)
        a = np.asarray(im.getchannel("A"))
        assert all(int(a[y,x]) == 0 for y,x in ((0,0),(0,-1),(-1,0),(-1,-1))), str(path)+" corner alpha"
        assert np.max(a) == 255, str(path)+" has no solid object"
        assert not np.any(a[0,:]) and not np.any(a[-1,:]) and not np.any(a[:,0]) and not np.any(a[:,-1]), str(path)+" touches frame edge"
        bbox = im.getchannel("A").getbbox()
        margin = min(bbox[0], bbox[1], size[0]-bbox[2], size[1]-bbox[3])
        assert margin >= 8, (str(path), "insufficient clearance", margin)
        return {"file":str(path.relative_to(OUT)),"size":list(im.size),"mode":im.mode,
                "corner_alpha":[int(a[0,0]),int(a[0,-1]),int(a[-1,0]),int(a[-1,-1])],
                "alpha_bbox":list(bbox),"minimum_clearance_px":margin,
                "transparent_pixel_fraction":round(float(np.mean(a==0)),5),
                "antialiased_pixel_count":int(np.sum((a>0)&(a<255)))}


report = {"scope":"heroes_only" if args.heroes_only else "all_deliverables",
          "renders":[],"sheets":[],"hero_to_final_pose":{},"all_passed":False}
heroes = {}
for name in NAMES:
    p = OUT/(name+"_hero.png")
    report["renders"].append(check(p,(1024,1024)))
    heroes[name] = Image.open(p).convert("RGBA")

# A single, honest contact of the five original hero renders composited on white.
contact = Image.new("RGB", (1800,1320), "white")
draw = ImageDraw.Draw(contact)
places = ((0,0),(600,0),(1200,0),(300,660),(900,660))
for name,label,(x,y) in zip(NAMES,LABELS,places):
    original = on_white(heroes[name]).resize((600,600),Image.Resampling.LANCZOS)
    contact.paste(original,(x,y))
    draw.text((x+300,y+610),label,font=font(25),fill="#0B1622",anchor="mt")
contact.save(OUT/"contact_white.png")
assert Image.open(OUT/"contact_white.png").size == (1800,1320)

if not args.heroes_only:
    review = Image.new("RGB", (2400,1760), "white")
    rd = ImageDraw.Draw(review)
    for row,name in enumerate(NAMES):
        assert sorted(p.name for p in (OUT/(name+"_spin")).glob("*.png")) == ["%04d.png"%i for i in range(30)]
        sheet = Image.new("RGBA", (3072,2560), (0,0,0,0))
        for i in range(30):
            p = OUT/(name+"_spin")/("%04d.png"%i)
            report["renders"].append(check(p,(512,512)))
            with Image.open(p) as im:
                # No mask here: copy all four channels without multiplying alpha.
                sheet.paste(im,((i%6)*512,(i//6)*512))
                thumb=on_white(im).resize((160,160),Image.Resampling.LANCZOS)
                xx=(i%15)*160
                yy=row*352+(i//15)*176
                review.paste(thumb,(xx,yy))
                rd.text((xx+7,yy+153),name+" %02d"%i,font=font(11),fill="#0B1622")
        dest=OUT/(name+"_spin_sheet.png")
        sheet.save(dest,compress_level=6)
        with Image.open(dest) as packed:
            assert packed.size == (3072,2560) and packed.mode == "RGBA"
            alpha=packed.getchannel("A")
            assert all(alpha.getpixel(xy)==0 for xy in ((0,0),(3071,0),(0,2559),(3071,2559)))
            # Check every original pixel against the matching sheet tile.
            for i in range(30):
                x,y=(i%6)*512,(i//6)*512
                tile=packed.crop((x,y,x+512,y+512))
                with Image.open(OUT/(name+"_spin")/("%04d.png"%i)) as original:
                    assert np.array_equal(np.asarray(tile),np.asarray(original)), (name,i,"sheet mismatch")
            report["sheets"].append({"file":dest.name,"size":[3072,2560],"mode":"RGBA",
                                     "all_30_tiles_pixel_identical":True})
        # Same final geometry/camera/light; differences from sample count and scale are measured.
        hero=on_white(heroes[name]).resize((512,512),Image.Resampling.LANCZOS)
        final=on_white(Image.open(OUT/(name+"_spin")/"0029.png").convert("RGBA"))
        diff=ImageStat.Stat(ImageChops.difference(hero,final)).mean
        assert max(diff) < 6, (name,"hero/final view mismatch",diff)
        report["hero_to_final_pose"][name]={"mean_RGB_absolute_difference_0_to_255":diff,
            "same_3D_pose":True,"explanation":"1024/64-sample hero versus 512/32-sample final frame"}
    review.save(OUT/"spin_review.png")
    report["all_passed"]=True

    if args.video:
        # White-background film preview only. The required PNGs and sprite sheets retain alpha.
        W,H=1800,1100
        command=["ffmpeg","-y","-v","error","-f","rawvideo","-pixel_format","rgb24",
                 "-video_size",f"{W}x{H}","-framerate","30","-i","pipe:0","-an",
                 "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
                 "-movflags","+faststart",str(OUT/"turntable_white.mp4")]
        proc=subprocess.Popen(command,stdin=subprocess.PIPE)
        positions=((75,0),(675,0),(1275,0),(375,550),(975,550))
        # 30 original moving frames + a 20-frame hero hold. Repeat once for a clear preview.
        for repeat in range(2):
            for n in list(range(30))+[29]*20:
                canvas=Image.new("RGB",(W,H),"white")
                d=ImageDraw.Draw(canvas)
                for name,label,(x,y) in zip(NAMES,LABELS,positions):
                    with Image.open(OUT/(name+"_spin")/("%04d.png"%n)) as im:
                        thumb=on_white(im).resize((450,450),Image.Resampling.LANCZOS)
                    canvas.paste(thumb,(x,y+20))
                    d.text((x+225,y+490),label,font=font(24),fill="#0B1622",anchor="mt")
                proc.stdin.write(canvas.tobytes())
        proc.stdin.close()
        assert proc.wait()==0,"FFmpeg preview failed"
        report["video"]={"file":"turntable_white.mp4","size":[W,H],"fps":30,
            "frames":100,"duration_seconds":100/30,"background":"white preview, PNG originals have alpha"}

if args.heroes_only:
    report["all_passed"]=True
path=OUT/("hero_verification.json" if args.heroes_only else "verification.json")
path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"verified_renders":len(report["renders"]),"verified_sheets":len(report["sheets"]),
      "all_passed":report["all_passed"],"contact":"contact_white.png"},ensure_ascii=False))
