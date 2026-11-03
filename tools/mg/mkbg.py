# mkbg.py — build a 1080x1920 30fps background track from a segment list (for render.js --bg)
# usage: python3 mkbg.py segs.json out.mp4
# segs.json: [{"type":"video","src":"a.mp4","ss":10,"dur":5.8,"pan":true},
#             {"type":"photo","src":"b.jpg","dur":4.5,"cx":.5,"cy":.5,"z0":1.0,"z1":1.12,"dx":0,"dy":-.1},
#             {"type":"color","dur":3.3,"color":"black"}]
import json, subprocess, sys, os, tempfile
sys.path.insert(0, "/home/claude/r3")
from photoclip import make
segs = json.load(open(sys.argv[1])); out = sys.argv[2]
tmp = tempfile.mkdtemp(prefix="mkbg_")
parts = []
for i, s in enumerate(segs):
    p = os.path.join(tmp, f"s{i:02d}.mp4"); d = float(s["dur"])
    if s["type"] == "photo":
        make(s["src"], p, d + 0.05, cx=s.get("cx", .5), cy=s.get("cy", .5), z0=s.get("z0", 1.0), z1=s.get("z1", 1.12), dx=s.get("dx", 0), dy=s.get("dy", 0))
    elif s["type"] == "color":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={s.get('color','black')}:s=1080x1920:r=30", "-t", str(d),
                        "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", p], check=True)
    else:
        vf = "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
        if s.get("pan", True):
            vf = f"fps=30,scale=1188:2112:force_original_aspect_ratio=increase,crop=1188:2112,crop=1080:1920:x='54+40*sin(t/3)':y='96-60*t/{d}',setsar=1"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s.get("ss", 0)), "-t", str(d + 0.05), "-i", s["src"], "-an", "-vf", vf,
                        "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", p], check=True)
    parts.append((p, d))
# exact-length concat: trim every part to its duration, then join
inp = []; fc = ""
for i, (p, d) in enumerate(parts):
    inp += ["-i", p]; fc += f"[{i}:v]trim=duration={d},setpts=PTS-STARTPTS,fps=30,format=yuv420p[v{i}];"
fc += "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[o]"
tmpout = out.replace(".mp4", ".part.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", fc, "-map", "[o]", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-r", "30", tmpout], check=True)
os.replace(tmpout, out)
print("ok", out, round(sum(d for _, d in parts), 2), "s")
