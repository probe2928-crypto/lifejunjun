import json, subprocess, sys, os, shutil
from PIL import Image, ImageDraw, ImageFont

FF = "/usr/local/bin/ffmpeg"
OUT = "/home/claude/ice"
SHEETS = os.path.join(OUT, "sheets")
os.makedirs(SHEETS, exist_ok=True)
META = os.path.join(OUT, "meta.jsonl")
TMP = "/tmp/claude-0/-home-claude/a9a6a4a9-e8ae-5216-aca3-ea5422819455/scratchpad/frames"

def done_set():
    s = set()
    if os.path.exists(META):
        for l in open(META):
            try: s.add(json.loads(l)["filename"])
            except Exception: pass
    return s

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", p],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None: raise RuntimeError("no video stream")
    a = any(s["codec_type"] == "audio" for s in d["streams"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd: rot = int(float(sd["rotation"]))
    if not rot and "rotate" in v.get("tags", {}): rot = -int(v["tags"]["rotate"])
    fr = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
    n, dd = fr.split("/"); fps = round(float(n) / float(dd), 3) if float(dd) else 0
    dur = float(d["format"].get("duration") or v.get("duration") or 0)
    ct = d["format"].get("tags", {}).get("creation_time") or v.get("tags", {}).get("creation_time")
    w, h = int(v["width"]), int(v["height"])
    dw, dh = (h, w) if abs(rot) % 180 == 90 else (w, h)
    return dict(filename=os.path.basename(p), path=p, duration=round(dur, 3), width=w, height=h,
                rotation=rot, display_width=dw, display_height=dh,
                orientation="portrait" if dh > dw else "landscape", fps=fps, has_audio=a,
                creation_time=ct, codec=v.get("codec_name"))

def sheet(p, m):
    base = os.path.splitext(m["filename"])[0]
    dur = m["duration"]
    os.makedirs(TMP, exist_ok=True)
    tiles = []
    font = ImageFont.load_default()
    for i in range(6):
        t = dur * (i + 0.5) / 6
        fp = os.path.join(TMP, f"f{i}.jpg")
        if os.path.exists(fp): os.remove(fp)
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", p, "-frames:v", "1",
                        "-vf", "scale='if(gt(iw,ih),320,-2)':'if(gt(iw,ih),-2,320)'", "-q:v", "4", fp],
                       capture_output=True)
        if not os.path.exists(fp):
            continue
        im = Image.open(fp).convert("RGB")
        dr = ImageDraw.Draw(im)
        txt = f"{t:.1f}s"
        bb = dr.textbbox((0, 0), txt, font=font)
        dr.rectangle([2, 2, bb[2] + 8, bb[3] + 6], fill=(0, 0, 0))
        dr.text((5, 4), txt, fill=(255, 255, 255), font=font)
        tiles.append(im)
    if not tiles: raise RuntimeError("no frames extracted")
    H = max(t.height for t in tiles)
    W = sum(t.width for t in tiles) + 4 * (len(tiles) - 1)
    out = Image.new("RGB", (W, H), (20, 20, 20))
    x = 0
    for t in tiles:
        out.paste(t, (x, (H - t.height) // 2)); x += t.width + 4
    sp = os.path.join(SHEETS, base + ".jpg")
    out.save(sp, quality=85)
    return sp, len(tiles)

if __name__ == "__main__":
    d = done_set()
    fails = []
    for p in sys.argv[1:]:
        fn = os.path.basename(p)
        if fn in d: continue
        try:
            m = probe(p)
            sp, n = sheet(p, m)
            m["sheet"] = sp; m["frames"] = n
            with open(META, "a") as f: f.write(json.dumps(m) + "\n")
            print("OK", fn, m["duration"], m["orientation"], m["has_audio"], n)
        except Exception as e:
            fails.append(fn); print("FAIL", fn, e)
            with open(os.path.join(OUT, "failures.txt"), "a") as f: f.write(f"{fn}\t{e}\n")
