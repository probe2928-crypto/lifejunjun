"""Reel-style editor: beat-synced cuts, punch zoom, flash, grade, grain, animated Korean typography.
spec = dict(name, W, H, bpm, seed, src_dir, meta, shots=[...], out_dir)
shot = dict(key, ss, beats, cx=0.5, vol=0, flash=False, zoom='in'|'out'|'none',
            hook=[lines] (first line may use [word] for highlight), cap='text with [hl]',
            chip='location', count='1', cta='text', fade_out=False)
"""
import json, os, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = "/home/claude/fonts/package/dist/public/static/"
F_BLACK = FD + "Pretendard-Black.otf"; F_XB = FD + "Pretendard-ExtraBold.otf"; F_SB = FD + "Pretendard-SemiBold.otf"
YEL = (255, 226, 64); BLK = (12, 12, 12); WHT = (255, 255, 255)
FPS = 30

def _parse(s):
    out = []; hl = False; buf = ""
    for ch in s:
        if ch == "[": out.append((buf, hl)); buf = ""; hl = True
        elif ch == "]": out.append((buf, hl)); buf = ""; hl = False
        else: buf += ch
    out.append((buf, hl)); return [(t, h) for t, h in out if t]

def text_png(path, lines, size, font=F_BLACK, W=1080, stroke=7, hl_box=True, align="center", box_all=None, line_gap=1.18):
    """lines: list of strings with [highlight]. highlight = black text on yellow box. Else white w/ black stroke."""
    f = ImageFont.truetype(font, size)
    pad_x, pad_y = int(size * 0.28), int(size * 0.12)
    H = int(len(lines) * size * line_gap + size * 0.8)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = int(size * 0.3)
    for ln in lines:
        parts = _parse(ln)
        widths = [d.textlength(t, font=f) + (2 * pad_x if h else 0) for t, h in parts]
        tw = sum(widths); x = (W - tw) / 2 if align == "center" else 60
        for (t, h), w in zip(parts, widths):
            if h or box_all:
                col = box_all or YEL
                d.rounded_rectangle([x, y - pad_y + size * 0.06, x + w, y + size + pad_y * 0.9], radius=int(size * 0.18), fill=col)
                d.text((x + pad_x, y), t, font=f, fill=BLK if col == YEL or col == WHT else WHT)
            else:
                # soft shadow
                sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
                ds.text((x + 4, y + 6), t, font=f, fill=(0, 0, 0, 150), stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
                im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
                d = ImageDraw.Draw(im)
                d.text((x, y), t, font=f, fill=WHT, stroke_width=stroke, stroke_fill=BLK)
            x += w
        y += int(size * line_gap)
    bb = im.getbbox() or (0, 0, W, H)
    im = im.crop((0, max(0, bb[1] - 10), W, min(H, bb[3] + 14)))
    im.save(path); return im.size

def chip_png(path, text, size=40, count=None):
    f = ImageFont.truetype(F_XB, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = d0.textlength(text, font=f)
    cw = 0
    if count is not None:
        fc = ImageFont.truetype(F_BLACK, int(size * 1.0)); cw = int(size * 1.5)
    pin = int(size * 0.9)
    W = int(tw + pin + size * 1.3 + cw); H = int(size * 1.75)
    im = Image.new("RGBA", (W + 20, H + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + W, 10 + H], radius=H // 2, fill=(15, 15, 18, 200))
    x = 10 + int(size * 0.45)
    if count is not None:
        d.ellipse([x - 6, 10 + (H - cw) // 2 + 2, x - 6 + cw - 6, 10 + (H + cw) // 2 - 4], fill=YEL)
        d.text((x - 6 + (cw - 6) / 2, 10 + H / 2), str(count), font=fc, fill=BLK, anchor="mm")
        x += cw
    else:
        # map pin
        cx, cy, r = x + pin / 2, 10 + H * 0.42, pin * 0.32
        d.polygon([(cx - r * 0.85, cy + r * 0.35), (cx + r * 0.85, cy + r * 0.35), (cx, cy + r * 2.0)], fill=YEL)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YEL); d.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], fill=(15, 15, 18))
        x += pin + int(size * 0.2)
    d.text((x, 10 + H / 2), text, font=f, fill=WHT, anchor="lm")
    im.save(path); return im.size

def load_meta(p):
    m = {}
    for l in open(p):
        d = json.loads(l); m[d["filename"]] = d
    return m

def find(src, key):
    c = [n for n in os.listdir(src) if key in n]; assert len(c) == 1, (key, c); return c[0]

def render_shot(spec, s, i, nframes, wd):
    W, H = spec["W"], spec["H"]; src = spec["src_dir"]
    name = find(src, s["key"]); m = spec["_meta"][name]
    dur = nframes / FPS
    portrait_src = m["display_height"] > m["display_width"]
    SW, SH = int(W * 1.18) // 2 * 2, int(H * 1.18) // 2 * 2
    cx = s.get("cx", 0.5)
    if (H > W) == portrait_src:
        base = f"scale={SW}:{SH}:force_original_aspect_ratio=increase:flags=lanczos,crop={SW}:{SH}"
    elif H > W:
        base = f"scale=-2:{SH},crop={SW}:{SH}:(iw-{SW})*{cx}:0"
    else:  # portrait in landscape: blurred bg
        base = (f"split[a][b];[a]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},boxblur=40:4,eq=brightness=-0.12[bg];"
                f"[b]scale=-2:{SH}[fg];[bg][fg]overlay=(W-w)/2:0")
    avail = s.get("max") or max(0.3, m["duration"] - s["ss"] - 0.05)
    speed = 1.0 if dur <= avail else max(s.get("minspeed", 0.5), avail / dur)
    tin = min(avail, dur * speed) + 0.15
    pre = ""
    if s.get("stab", True):
        trf = f"{wd}/s{i}.trf"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(s["ss"]), "-t", f"{tin:.3f}", "-i", f"{src}/{name}",
                        "-vf", f"vidstabdetect=shakiness=7:accuracy=15:result={trf}", "-f", "null", "-"], check=True)
        pre += f"vidstabtransform=input={trf}:smoothing=22:zoom=3:optzoom=0:interpol=bicubic,unsharp=5:5:0.5,"
    if speed < 1.0: pre += f"setpts=PTS/{speed:.4f},"
    base = pre + base
    z = s.get("zoom", "in")
    if z == "out": zexp = f"1.12-0.10*on/{nframes}"
    elif z == "none": zexp = "1.0"
    else: zexp = f"if(lt(on,5),1.13-0.024*on,1.01+0.07*(on-5)/{nframes})"
    vf = (f"{base},fps={FPS},tpad=stop_mode=clone:stop_duration=4,zoompan=z='{zexp}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
          f"eq=contrast=1.08:saturation=1.2:brightness=0.005,colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02,"
          f"vignette=PI/5.5,noise=alls=3:allf=t,format=yuv420p")
    # 휩 전환(2026-11-09 2회차): 컷 경계 앞뒤 2~3프레임에 가로 방향 모션 블러 → 하드컷보다 매끄럽게
    if s.get("_whip_in"):
        vf += f",dblur=angle=0:radius=70:enable='lt(n,2)',dblur=angle=0:radius=28:enable='between(n,2,3)'"
    if s.get("_whip_out"):
        vf += f",dblur=angle=0:radius=28:enable='between(n,{nframes-4},{nframes-3})',dblur=angle=0:radius=70:enable='gte(n,{nframes-2})'"
    if s.get("flash"): vf += ",fade=t=in:st=0:d=0.13:color=white"
    if s.get("fade_out"): vf += f",fade=t=out:st={dur-0.5:.3f}:d=0.5"
    # overlays
    ovs = []
    if s.get("hook"):
        p = f"{wd}/t{i}_hook.png"; w, h = text_png(p, s["hook"], int(W * (0.118 if H > W else 0.06)), W=W)
        y = int(H * 0.19) if H > W else int(H * 0.30)
        ovs.append((p, y, 0.0, "pop"))
    if s.get("cap"):
        p = f"{wd}/t{i}_cap.png"; text_png(p, [s["cap"]] if isinstance(s["cap"], str) else s["cap"], int(W * (0.074 if H > W else 0.042)), font=F_BLACK, W=W, stroke=6)
        y = int(H * s.get("cap_y", 0.60)) if H > W else int(H * 0.74)
        ovs.append((p, y, 0.12, "up"))
    if s.get("chip") or s.get("count"):
        p = f"{wd}/t{i}_chip.png"; cw, ch = chip_png(p, s.get("chip", ""), size=int(W * (0.054 if H > W else 0.024)), count=s.get("count"))
        ovs.append((p, int(H * 0.155) if H > W else int(H * 0.08), 0.05, "chipL"))
    if s.get("cta"):
        p = f"{wd}/t{i}_cta.png"; text_png(p, s["cta"], int(W * (0.09 if H > W else 0.05)), W=W)
        ovs.append((p, int(H * 0.40), 0.25, "pop"))
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(s["ss"]), "-t", f"{tin:.3f}", "-i", f"{src}/{name}"]
    for p, *_ in ovs: cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
    fc = f"[0:v]{vf}[v0]"; last = "v0"
    for k, (p, y, delay, anim) in enumerate(ovs, start=1):
        a = f"[{k}:v]format=rgba,fade=t=in:st={delay}:d=0.18:alpha=1"
        if s.get("fade_out"): a += f",fade=t=out:st={dur-0.5:.3f}:d=0.4:alpha=1"
        a += f"[o{k}]"
        if anim == "chipL":
            xx = f"'if(lt(t,{delay}+0.25),-w+(t-{delay})/0.25*(w+48),48)'"; yy = str(y)
        elif anim == "up":
            xx = "(W-w)/2"; yy = f"'{y}+50*max(0,1-(t-{delay})/0.22)'"
        else:
            xx = "(W-w)/2"; yy = f"'{y}-30*max(0,1-(t-{delay})/0.2)'"
        fc += f";{a};[{last}][o{k}]overlay=x={xx}:y={yy}:eval=frame[v{k}]"; last = f"v{k}"
    vol = s.get("vol", 0.0)
    nin = len(ovs) + 1
    ain = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]; sil = nin; nin += 1
    if m["has_audio"] and vol > 0:
        fc += f";[0:a]aresample=48000,aformat=channel_layouts=stereo,atempo={max(0.5,speed):.4f},volume={vol},afade=t=in:d=0.05,afade=t=out:st={dur-0.1:.3f}:d=0.1[ao]"
    else:
        fc += f";[{sil}:a]anull[ao]"
    if s.get("vo"):
        ain += ["-i", s["vo"]]
        fc += f";[{nin}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=120|120,volume=1.6[vo];[ao][vo]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        fc += ";[ao]anull[a]"
    amap = ["-map", "[a]"]
    out = f"{wd}/{i:02d}.mp4"
    cmd = cmd + ain + ["-filter_complex", fc, "-map", f"[{last}]"] + amap + [
        "-frames:v", str(nframes), "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out]
    subprocess.run(cmd, check=True)
    return out

def build(spec):
    spec["_meta"] = load_meta(spec["meta"])
    wd = f"{spec['out_dir']}/work_{spec['name']}"; os.makedirs(wd, exist_ok=True)
    spb = 60 / spec["bpm"]; cum = 0; prev = 0; parts = []
    vo = spec.get("vo")
    span = spec.get("vo_span", False)  # 2026-11-09: 멘트 하나가 여러 컷에 걸쳐 흐름(한 컷 길게 끄는 문제 해결)
    def vlen(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
    shots = spec["shots"]
    if vo and span:
        idx = [i for i, s in enumerate(shots) if s.get("vo_i") is not None]
        for j, i in enumerate(idx):
            grp = list(range(i, idx[j + 1] if j + 1 < len(idx) else len(shots)))
            need = math.ceil((vlen(f"{vo}_{shots[i]['vo_i']:02d}.mp3") + 0.35) / spb)
            have = sum(shots[k]["beats"] for k in grp)
            if have < need: shots[grp[0]]["beats"] += need - have
    vo_marks = []
    for i, s in enumerate(shots):  # whip: 플래시 없는 컷 전환은 기본 휩(spec whip=False 로 끔, 컷별 whip=False)
        if i > 0 and spec.get("whip", True) and not s.get("flash") and s.get("whip", True) and not shots[i-1].get("fade_out"):
            s["_whip_in"] = True; shots[i-1]["_whip_out"] = True
    for i, s in enumerate(shots):
        if vo and s.get("vo_i") is not None:
            p = f"{vo}_{s['vo_i']:02d}.mp3"
            if span: vo_marks.append((prev / FPS, p))
            else:
                s["vo"] = p; s["beats"] = max(s["beats"], math.ceil((vlen(p) + 0.35) / spb))
        cum += s["beats"]; end = round(cum * spb * FPS); n = end - prev; prev = end
        parts.append(render_shot(spec, s, i, n, wd)); print(spec["name"], i, s["key"], n, flush=True)
    total = prev / FPS
    open(f"{wd}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{wd}/list.txt", "-c", "copy", f"{wd}/joined.mp4"], check=True)
    if vo_marks:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", f"{wd}/joined.mp4"]
        fc = ""
        for k, (t0, p) in enumerate(vo_marks, start=1):
            cmd += ["-i", p]; ms = int(t0 * 1000) + 120
            fc += f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.6[v{k}];"
        fc += "[0:a]" + "".join(f"[v{k}]" for k in range(1, len(vo_marks) + 1)) + f"amix=inputs={len(vo_marks)+1}:duration=first:normalize=0[a]"
        subprocess.run(cmd + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", f"{wd}/joined_vo.mp4"], check=True)
        os.replace(f"{wd}/joined_vo.mp4", f"{wd}/joined.mp4")
    mp = f"{wd}/beat.wav"
    subprocess.run(["python3", "/home/claude/reel/beat.py", str(total + 1), mp, str(spec["bpm"]), str(spec["seed"]), str(spec.get("root", 45))], check=True)
    outp = f"{spec['out_dir']}/{spec['name']}.mp4"
    # 하단 진행 바(2026-11-09): 끝까지 보게 만드는 얇은 노란 바. spec progress=False 로 끔.
    vmap = ["-map", "0:v", "-c:v", "copy"]; vf_pb = ""
    if spec.get("progress", True):
        bh = max(8, spec["H"] // 200)
        vf_pb = (f"[0:v]drawbox=x=0:y=ih-{bh}:w=iw:h={bh}:color=black@0.35:t=fill,"
                 f"drawbox=x=0:y=ih-{bh}:w='iw*t/{total:.3f}':h={bh}:color=0xFFE240@0.95:t=fill[pv];")
        vmap = ["-map", "[pv]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{wd}/joined.mp4", "-i", mp, "-filter_complex",
                    vf_pb + f"[1:a]atrim=0:{total},afade=t=out:st={total-1.2}:d=1.2,volume=0.75[m0];[0:a]asplit[o][k];[m0][k]sidechaincompress=threshold=0.04:ratio=6:attack=15:release=350[m];[o][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.92[a]",
                    ] + vmap + ["-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", outp], check=True)
    print("DONE", outp, round(total, 2))
