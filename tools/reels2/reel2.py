#!/usr/bin/env python3
"""인생준준 tip reel v2 — real footage + documentary lower-third text (style "doc", default) or the old highlight-box look (style "box").

usage: python reel2.py spec.json [--sheet]      full render (needs local clips + music file)
       python reel2.py spec.json --layout out.jpg  text-layout check only (no footage needed; grey stand-in)
  writes spec["out"] (mp4) + spec["cover"] (jpg, hook frame) [+ <out>_sheet.jpg]

In the repo, specs use "clip":"mixkit:<id>" (see tools/reels2/clips.json + catsheets/) and "music":"<key of
tools/reels2/music.json>"; Sejun's PC (post_queue.py) downloads those, fills bpm/music_ss, renders and posts.
Text budget (fits one line at full size): lines ≤ 13 chars, hl ≤ 12 chars, body ≤ 16 chars, max 2 body lines.

spec: {"id","out","cover","bpm":100,
       "music": "music/x.mp3", "music_ss": 0.0,
       "scenes":[
         {"kind":"hook","clip":"clips/608.mp4","ss":1.0,"beats":4,"cx":.5,"cy":.5,
          "kicker":"러닝 상식 체크","lines":["달리기 전 스트레칭,"],"hl":"부상 예방 효과 거의 없음","sub":"26,610명 데이터가 말해요"},
         {"kind":"tip","clip":…,"n":1,"of":4,"lines":["정적 스트레칭"],"hl":"부상 예방 ✕","body":["25개 연구 · 26,610명"],"src":"BJSM 2014"},
         {"kind":"cta","clip":…,"lines":["뛰기 전에 다시 보게"],"hl":"저장해두기","sub":"같이 뛰는 친구한테 보내기"}]}
clip ss = start second inside the source clip; cx/cy = horizontal/vertical crop anchor 0..1.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
FD = os.environ.get("LJ_FONTS") or next((p for p in (os.path.join(HERE, "fonts"), os.path.join(HERE, "pret", "public", "static"))
                                          if os.path.exists(os.path.join(p, "Pretendard-Black.otf"))), os.path.join(HERE, "fonts"))
LIME = (214, 255, 64, 255); INK = (14, 14, 14, 255); WHITE = (255, 255, 255, 255)
SOFT = (255, 255, 255, 215)


def F(w, s): return ImageFont.truetype(os.path.join(FD, f"Pretendard-{w}.otf"), s)


def run(args):
    r = subprocess.run(args, capture_output=True)
    if r.returncode: sys.exit(r.stderr.decode("utf-8", "ignore")[-2000:])


# ---------- text layers ----------
def shadowed(im, blur=14, op=.62, dy=5):
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, dy)); out.alpha_composite(im)
    return out


def meas_size(rows, txt): return next(r[2].size for r in rows if r[1] == txt)


def text_block(rows, align="center", pad=40):
    """rows: list of (kind, text, font, fill, extra). kind 'txt' or 'hl' (highlight box) or 'pill'.
    returns RGBA image (width W) and list of (y0,y1) per row for staggered reveal."""
    meas = []
    for kind, txt, f, fill, gap in rows:
        room = 940 if kind == "hl" else 980
        while f.getbbox(txt)[2] - f.getbbox(txt)[0] + (44 if kind == "hl" else 0) > room and f.size > 30:
            f = f.font_variant(size=f.size - 4)
        if f.size < meas_size(rows, txt): print(f"  shrunk to {f.size}px: {txt}")
        bb = f.getbbox(txt); tw, th = bb[2] - bb[0], f.size
        if kind == "hl": bw, bh = tw + 44, int(th * 1.32)
        elif kind == "pill": bw, bh = tw + 36, int(th * 1.55)
        else: bw, bh = tw, int(th * 1.22)
        meas.append((kind, txt, f, fill, gap, bb, bw, bh))
    total = sum(m[7] + m[4] for m in meas) + pad * 2
    im = Image.new("RGBA", (W, total), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = pad; spans = []
    for kind, txt, f, fill, gap, bb, bw, bh in meas:
        x = (W - bw) // 2 if align == "center" else 84
        if kind == "hl":
            d.rounded_rectangle((x, y, x + bw, y + bh), radius=14, fill=LIME)
            d.text((x + 22 - bb[0], y + (bh - f.size) // 2 - bb[1] + int(f.size * .06)), txt, font=f, fill=INK)
        elif kind == "pill":
            d.rounded_rectangle((x, y, x + bw, y + bh), radius=bh // 2, fill=(14, 14, 14, 190))
            d.text((x + 18 - bb[0], y + (bh - f.size) // 2 - bb[1] + int(f.size * .08)), txt, font=f, fill=fill)
        else:
            d.text((x - bb[0], y), txt, font=f, fill=fill)
        spans.append((y, y + bh)); y += bh + gap
    return im, spans


# ---------- "doc" style (default since 2026-10-27): documentary lower-third, no boxes ----------
DOC_X, DOC_ROOM = 84, 860          # keep clear of Instagram's right-hand buttons
DOC_BOTTOM = 1590                  # keep clear of Instagram's caption area


def _fit(txt, f, room):
    while f.getlength(txt) > room and f.size > 26: f = f.font_variant(size=f.size - 2)
    return f


def doc_layers(sc):
    k = sc["kind"]; rows = []   # (kind, text, font, rgba, gap_after)
    tag = sc.get("tag") or sc.get("_tag") or (sc.get("kicker") if k == "hook" else "")
    if k == "tip": tag = (tag + "   " if tag else "") + f"{sc['n']:02d} / {sc['of']:02d}"
    if tag: rows.append(("track", tag.upper(), F("SemiBold", 30), (255, 255, 255, 205), 30))
    if sc.get("big"): rows.append(("txt", sc["big"], F("Medium", 230), WHITE, 18))
    for ln in sc.get("lines", []) + ([sc["hl"]] if sc.get("hl") else []):
        rows.append(("txt", ln, F("Bold", 68), WHITE, 14))
    if rows and rows[-1][4] == 14: rows[-1] = rows[-1][:4] + (30,)
    for ln in sc.get("body", []) + ([sc["sub"]] if sc.get("sub") else []):
        rows.append(("txt", ln, F("Medium", 42), (255, 255, 255, 215), 12))
    if sc.get("src"): rows.append(("txt", "출처 · " + sc["src"], F("Medium", 28), (255, 255, 255, 150), 0))
    if k == "cta": rows.append(("rule", "인생준준 · 직접 다녀온 여행" if "brand" not in sc else sc["brand"], F("SemiBold", 28), (255, 255, 255, 185), 0))
    meas = []
    for kind, txt, f, fill, gap in rows:
        if kind == "track":
            w = sum(f.getlength(c) + 6 for c in txt)
            while w > DOC_ROOM and f.size > 20:
                f = f.font_variant(size=f.size - 2); w = sum(f.getlength(c) + 6 for c in txt)
        else:
            f0 = f; f = _fit(txt, f, DOC_ROOM - (56 if kind == "rule" else 0))
            if f.size < f0.size: print(f"  shrunk to {f.size}px: {txt}")
        asc, desc = f.getmetrics(); meas.append((kind, txt, f, fill, gap, asc + desc))
    pad = 40; total = sum(m[5] + m[4] for m in meas) + pad * 2
    im = Image.new("RGBA", (W, total), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = pad; spans = []
    for kind, txt, f, fill, gap, h in meas:
        x = DOC_X
        if kind == "track":
            for c in txt: d.text((x, y), c, font=f, fill=fill); x += f.getlength(c) + 6
        elif kind == "rule":
            d.rectangle((x, y + h // 2 - 2, x + 40, y + h // 2 + 1), fill=fill); d.text((x + 56, y), txt, font=f, fill=fill)
        else:
            d.text((x - (8 if f.size > 150 else 0), y), txt, font=f, fill=fill)
        spans.append((y, y + h)); y += h + gap
    im = shadowed(im, blur=16, op=.55, dy=4)
    top = int(sc.get("bottom", DOC_BOTTOM)) - (total - pad)
    return np.asarray(im).astype(np.float32) / 255, spans, top


def grad_for(style):
    yy = np.linspace(0, 1, H)[:, None, None]
    if style == "box":
        return (0.50 * np.clip(1 - (yy - .12) / .55, 0, 1) ** 1.4 + 0.10).astype(np.float32)
    return (0.80 * np.clip((yy - .40) / .60, 0, 1) ** 1.5 + 0.04).astype(np.float32)


def prep_style(spec):
    tag = spec.get("tag", "")
    for sc in spec["scenes"]:
        sc["_style"] = spec.get("style", "doc"); sc.setdefault("_tag", tag)


def layers_for(sc):
    if sc.get("_style", "doc") != "box": return doc_layers(sc)
    return box_layers(sc)


def box_layers(sc):
    k = sc["kind"]; rows = []
    if k == "hook":
        if sc.get("kicker"): rows.append(("pill", sc["kicker"], F("Bold", 38), LIME, 26))
        for ln in sc.get("lines", []): rows.append(("txt", ln, F("Black", 98), WHITE, 10))
        if sc.get("hl"): rows.append(("hl", sc["hl"], F("Black", 98), INK, 28))
        if sc.get("sub"): rows.append(("txt", sc["sub"], F("SemiBold", 48), SOFT, 0))
        top = sc.get("top", .20)
    elif k == "tip":
        rows.append(("pill", f"{sc['n']} / {sc['of']}", F("Bold", 40), LIME, 26))
        for ln in sc.get("lines", []): rows.append(("txt", ln, F("Black", 88), WHITE, 10))
        if sc.get("hl"): rows.append(("hl", sc["hl"], F("Black", 88), INK, 30))
        for ln in sc.get("body", []): rows.append(("txt", ln, F("SemiBold", 50), WHITE, 8))
        if sc.get("src"): rows.append(("txt", "출처 · " + sc["src"], F("Medium", 32), (255, 255, 255, 170), 0))
        top = sc.get("top", .17)
    else:
        for ln in sc.get("lines", []): rows.append(("txt", ln, F("Black", 92), WHITE, 10))
        if sc.get("hl"): rows.append(("hl", sc["hl"], F("Black", 104), INK, 30))
        if sc.get("sub"): rows.append(("txt", sc["sub"], F("SemiBold", 50), WHITE, 22))
        rows.append(("txt", sc.get("brand", "인생준준 · RUN & TREK"), F("Bold", 34), (255, 255, 255, 190), 0))
        top = sc.get("top", .24)
    im, spans = text_block(rows)
    im = shadowed(im)
    return np.asarray(im).astype(np.float32) / 255, spans, int(H * top)


# ---------- base footage ----------
def build_base(spec, work):
    bpm = spec.get("bpm", 100); segs = []
    for k, sc in enumerate(spec["scenes"]):
        dur = sc["beats"] * 60 / bpm; sc["_dur"] = dur
        out = os.path.join(work, f"seg{k:02d}.mp4"); segs.append(out)
        cx, cy = sc.get("cx", .5), sc.get("cy", .5); sp = sc.get("speed", 1.0)
        vf = (f"setpts=PTS/{sp},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})*{cy},fps={FPS},"
              f"eq=contrast=1.05:saturation=1.10:brightness=-0.01,cas=0.35")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(sc.get("ss", 0)), "-t", f"{dur * sp + .2:.3f}", "-i", sc["clip"],
             "-vf", vf, "-t", f"{dur:.3f}", "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", out])
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f: f.writelines(f"file '{os.path.abspath(s)}'\n" for s in segs)
    base = os.path.join(work, "base.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])
    return base


def ease(x): x = min(max(x, 0.), 1.); return 1 - (1 - x) ** 3


def render(spec):
    work = os.path.join(HERE, "work", spec["id"]); os.makedirs(work, exist_ok=True)
    base = build_base(spec, work)
    starts, t = [], 0.
    for sc in spec["scenes"]: starts.append(t); t += sc["_dur"]
    total = t; N = int(round(total * FPS))
    prep_style(spec); L = [layers_for(sc) for sc in spec["scenes"]]
    # legibility gradient: dark top 65 % fading out
    yy = np.linspace(0, 1, H)[:, None, None]
    prep_style(spec); grad = grad_for(spec.get("style", "doc"))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    vid = os.path.join(work, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-profile:v", "high",
                            "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    cover_frame = None
    for i in range(N):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        tt = i / FPS; k = max(j for j in range(len(starts)) if starts[j] <= tt + 1e-6); lt = tt - starts[k]
        fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
        # punch-in on every cut (1.07 -> 1.0 in 0.25 s)
        z = 1 + .07 * (1 - ease(lt / .25))
        if z > 1.001:
            im = Image.fromarray((fr * 255).astype(np.uint8)); cw, ch = int(W / z), int(H / z)
            im = im.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)
            fr = np.asarray(im).astype(np.float32) / 255
        fr = fr * (1 - grad)
        lay, spans, top = L[k]; kind = spec["scenes"][k]["kind"]
        # staggered row reveal (hook row 0..n visible from frame 0 so the first frame already hooks)
        for r, (y0, y1) in enumerate(spans):
            delay = 0 if kind == "hook" else .06 + r * .09
            a = ease((lt - delay) / .16) if kind != "hook" else 1.
            if a <= 0: continue
            off = int((1 - a) * 28); pad = 40
            ys, ye = max(0, y0 - pad + 0), min(lay.shape[0], y1 + pad)
            seg = lay[ys:ye]; Y0 = top + ys + off; Y1 = Y0 + seg.shape[0]
            if Y1 > H: seg = seg[:H - Y0]; Y1 = H
            al = seg[..., 3:4] * a
            fr[Y0:Y1] = fr[Y0:Y1] * (1 - al) + seg[..., :3] * al
        out = (np.clip(fr, 0, 1) * 255).astype(np.uint8)
        if i == int(.9 * FPS): cover_frame = out.copy()
        enc.stdin.write(out.tobytes())
    enc.stdin.close(); enc.wait()
    dec.stdout.close(); dec.kill(); dec.wait()   # base may hold a few extra frames: never block on them
    # audio: music trimmed, faded, loudness-normalised
    out = spec["out"]; os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if spec.get("music"):
        af = f"atrim=0:{total:.3f},afade=t=in:d=0.03,afade=t=out:st={total - .7:.3f}:d=0.7,loudnorm=I=-14:TP=-1.5:LRA=9"
        run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-ss", str(spec.get("music_ss", 0)), "-i", spec["music"],
             "-filter_complex", f"[1:a]{af},aresample=48000[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-c", "copy", "-movflags", "+faststart", out])
    if cover_frame is not None and spec.get("cover"):
        Image.fromarray(cover_frame).save(spec["cover"], quality=93)
    print("wrote", out, f"{total:.1f}s", os.path.getsize(out) // 1024, "KB")
    return out, total


def sheet(spec, out, total):
    starts, t = [], 0.
    for sc in spec["scenes"]: starts.append(t + sc["_dur"] * .7); t += sc["_dur"]
    ims = []
    for k, ts in enumerate(starts):
        p = os.path.join(HERE, "work", spec["id"], f"s{k}.jpg")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ts:.2f}", "-i", out, "-frames:v", "1", p]); ims.append(Image.open(p).resize((360, 640)))
    S = Image.new("RGB", (360 * len(ims), 640))
    for k, im in enumerate(ims): S.paste(im, (360 * k, 0))
    p = os.path.splitext(out)[0] + "_sheet.jpg"; S.save(p, quality=85); print("sheet", p)


def layout(spec, path):
    """Text overlays of every scene on a grey stand-in frame (reports any row the auto-fit had to shrink)."""
    yy = np.linspace(0, 1, H)[:, None, None]
    prep_style(spec); grad = grad_for(spec.get("style", "doc"))
    ims = []
    for sc in spec["scenes"]:
        fr = np.full((H, W, 3), .55, np.float32) * (1 - grad)
        lay, spans, top = layers_for(sc)
        h = min(lay.shape[0], H - top); al = lay[:h, :, 3:4]
        fr[top:top + h] = fr[top:top + h] * (1 - al) + lay[:h, :, :3] * al
        ims.append(Image.fromarray((fr * 255).astype(np.uint8)).resize((360, 640)))
    S = Image.new("RGB", (360 * len(ims), 640))
    for k, im in enumerate(ims): S.paste(im, (360 * k, 0))
    S.save(path, quality=85); print("layout", path)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    if "--layout" in sys.argv:
        layout(spec, sys.argv[sys.argv.index("--layout") + 1]); sys.exit(0)
    o, tot = render(spec)
    if "--sheet" in sys.argv: sheet(spec, o, tot)
