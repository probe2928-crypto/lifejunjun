#!/usr/bin/env python3
"""reel3 — cue-based reel compositor (2026-10-27).

Layouts
  letterbox : black canvas, fixed headline on top, footage box in the middle, brand at the bottom,
              small caption box synced to the voice (the common Korean shorts template).
  full      : full-bleed footage, big outlined captions synced to the voice.
Overlays    : arrow (points at something), tag (label box), badge (year pill), endcard (place reveal).
Text markup : wrap words in [brackets] to colour them with the accent colour.

usage: python reel3.py spec.json [--sheet]
"""
import json, os, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))


def run(a):
    r = subprocess.run(a, capture_output=True)
    if r.returncode: sys.exit(r.stderr.decode("utf-8", "ignore")[-1500:])


_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc:
        p = path if os.path.isabs(path) else os.path.join(spec_fontdir, path)
        _fc[k] = ImageFont.truetype(p, size)
    return _fc[k]


def segs(line):
    out, cur, em = [], "", False
    for ch in line:
        if ch in "[]":
            if cur: out.append((cur, em))
            cur, em = "", ch == "["
        else: cur += ch
    if cur: out.append((cur, em))
    return out


def fit(f, txt, room, path):
    s = f.size
    while f.getlength(txt) > room and s > 24:
        s -= 2; f = font(path, s)
    return f


def text_img(lines, fpath, size, fill=(255, 255, 255, 255), accent=(255, 214, 64, 255), stroke=0, stroke_fill=(0, 0, 0, 255),
             gap=12, room=980, shadow=0.0, align="center", width=W, upto=None):
    """Render lines (with [accent] markup) into an RGBA image of width `width`. returns (img, row_spans)."""
    rows = []
    for ln in lines:
        plain = ln.replace("[", "").replace("]", "")
        f = fit(font(fpath, size), plain, room, fpath)
        asc, desc = f.getmetrics(); rows.append((ln, f, asc + desc + stroke * 2))
    pad = 30 + stroke
    total = sum(r[2] for r in rows) + gap * (len(rows) - 1) + pad * 2
    im = Image.new("RGBA", (width, total), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = pad; spans = []; wcount = 0
    for ln, f, h in rows:
        newword = True
        sg = segs(ln); tw = sum(f.getlength(t) for t, _ in sg)
        x = (width - tw) / 2 if align == "center" else pad
        for t, em in sg:
            for piece in re.split(r"( )", t):  # word-level so captions can reveal word by word
                if piece == "":
                    continue
                if piece == " ":
                    newword = True
                elif newword:  # words split by spaces only: "[만타가오리]를" is one word
                    wcount += 1; newword = False
                if upto is None or (piece != " " and wcount <= upto):
                    d.text((x, y + stroke), piece, font=f, fill=accent if em else fill, stroke_width=stroke, stroke_fill=stroke_fill)
                x += f.getlength(piece)
        spans.append((y, y + h)); y += h + gap
    if shadow:
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * shadow))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a)
        out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 4)); out.alpha_composite(im); im = out
    return im, spans


def pill(txt, fpath, size, fg, bg, padx=26, pady=14, radius=None):
    f = font(fpath, size); bb = f.getbbox(txt); tw, th = bb[2] - bb[0], size
    w, h = int(tw + padx * 2), int(th * 1.25 + pady * 2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius if radius is not None else h // 2, fill=bg)
    d.text((padx - bb[0], (h - th) / 2 - bb[1] + th * .08), txt, font=f, fill=fg)
    return im


def arrow(length=170, color=(235, 40, 40, 255), width=16):
    im = Image.new("RGBA", (length + 40, 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((10, 40, length - 20, 40), fill=color, width=width)
    d.polygon([(length + 30, 40), (length - 34, 6), (length - 34, 74)], fill=color)
    sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .45))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(sh)
    out.alpha_composite(s, (0, 3)); out.alpha_composite(im); return out


def magnifier(src, box, r, ring):
    """Circular zoom bubble of box=(x0,y0,x1,y1) from a still image, with a coloured ring."""
    s = Image.open(src).convert("RGB").crop(tuple(box)).resize((2 * r, 2 * r), Image.LANCZOS)
    from PIL import ImageEnhance
    s = ImageEnhance.Sharpness(s.filter(ImageFilter.UnsharpMask(3, 120, 2))).enhance(1.3)
    pad = 24; im = Image.new("RGBA", (2 * r + pad * 2, 2 * r + pad * 2), (0, 0, 0, 0))
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((pad - 4, pad + 6, pad + 2 * r + 4, pad + 2 * r + 14), fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    im.paste(s, (pad, pad), m)
    ImageDraw.Draw(im).ellipse((pad - 6, pad - 6, pad + 2 * r + 6, pad + 2 * r + 6), outline=ring, width=14)
    return im


def hblur(a, r):
    """horizontal box blur of HxWx3 uint8 array with radius r (motion blur for whip pans)."""
    r = int(r)
    if r < 1: return a
    f = a.astype(np.float32); c = np.cumsum(np.pad(f, ((0, 0), (r + 1, r), (0, 0)), mode="edge"), axis=1)
    return ((c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)).clip(0, 255).astype(np.uint8)


def trans_fx(img, mode, p, bw, bh):
    """p in 0..1 = strength (1 at the cut). mode 'zoom' (zoom-through) or 'whip' (fast pan)."""
    if p <= 0.001: return img
    if mode == "zoom":
        s = 1 + .6 * p ** 1.6; cw, ch = int(bw / s), int(bh / s)
        img = img.crop(((bw - cw) // 2, (bh - ch) // 2, (bw - cw) // 2 + cw, (bh - ch) // 2 + ch)).resize((bw, bh), Image.BILINEAR)
        return img.filter(ImageFilter.GaussianBlur(12 * p * p)) if p > .2 else img
    if mode == "whip":
        sh = int(p * p * bw * .4); a = np.asarray(img)
        a = np.pad(a, ((0, 0), (sh, 0), (0, 0)), mode="edge")[:, :bw] if sh else a
        return Image.fromarray(hblur(a, 50 * p))
    return img


def ease(x): x = min(max(x, 0.), 1.); return 1 - (1 - x) ** 3


def paste(canvas, im, x, y, alpha=1.0, scale=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
        x += (im.width / scale - im.width) / 2 if False else 0
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x, y = int(x), int(y)
    if x < 0 or y < 0:  # crop off-canvas parts (alpha_composite needs a non-negative dest)
        im = im.crop((max(0, -x), max(0, -y), im.width, im.height)); x, y = max(x, 0), max(y, 0)
    if x >= canvas.width or y >= canvas.height or im.width == 0 or im.height == 0: return
    im = im.crop((0, 0, min(im.width, canvas.width - x), min(im.height, canvas.height - y)))
    canvas.alpha_composite(im, (x, y))


# ---------------- base footage ----------------
def build_base(spec, work, bw, bh):
    segs_ = []
    for k, s in enumerate(spec["shots"]):
        out = os.path.join(work, f"shot{k:02d}.mp4"); segs_.append(out)
        cx, cy = s.get("cx", .5), s.get("cy", .5)
        vf = ((s["pre"] + ",") if s.get("pre") else "") + (f"scale={bw}:{bh}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={bw}:{bh}:(iw-{bw})*{cx}:(ih-{bh})*{cy},fps={FPS},eq=contrast=1.04:saturation=1.08"
              + ("," + s["vf"] if s.get("vf") else "") + f",tpad=stop_mode=clone:stop_duration={s['dur'] + 1:.2f},format=yuv420p")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(s.get("ss", 0)), "-t", f"{s['dur'] + .2:.3f}", "-i", s["clip"],
             "-vf", vf, "-frames:v", str(int(round(s['dur'] * FPS))), "-an", "-c:v", "libx264", "-crf", "14", "-preset", "fast", out])
    lst = os.path.join(work, "list.txt")
    open(lst, "w").writelines(f"file '{os.path.abspath(x)}'\n" for x in segs_)
    base = os.path.join(work, "base.mp4")
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])
    return base


def snap_timeline(spec):
    """Shot lengths in whole frames; caption/overlay times on the frame grid, glued to cuts within 2 frames."""
    acc = 0; starts = []
    for s in spec["shots"]:
        n = max(1, int(round(s["dur"] * FPS))); starts.append(acc); s["dur"] = n / FPS; acc += n
    cutt = [n / FPS for n in starts] + [acc / FPS]
    def sn(x):
        n = int(round(x * FPS))
        for c in cutt:
            if abs(c - x) <= 2.01 / FPS: return c
        return n / FPS
    for c in spec.get("subs", []):
        c["t0"] = sn(c["t0"]); c["t1"] = sn(c["t1"])
        if c.get("wt"): c["wt"] = [round(w * FPS) / FPS for w in c["wt"]]
    for o in spec.get("overlays", []):
        if "t0" in o: o["t0"] = sn(o["t0"])
        if "t1" in o: o["t1"] = sn(o["t1"])


def render(spec):
    global spec_fontdir
    spec_fontdir = spec.get("fontdir", HERE)
    work = os.path.join(spec.get("workdir", "/tmp"), "r3_" + spec["id"]); os.makedirs(work, exist_ok=True)
    st = spec.get("style", {})
    lay = spec.get("layout", "full")
    snap_timeline(spec)
    if lay == "letterbox":
        box = spec.get("box", [0, 440, 1080, 1080])
    else:
        box = [0, 0, W, H]
    bx, by, bw, bh = box
    base = build_base(spec, work, bw, bh)
    total = sum(s["dur"] for s in spec["shots"]); N = int(round(total * FPS))
    shot_starts = []; t = 0
    for s in spec["shots"]: shot_starts.append(round(t * FPS) / FPS); t += s["dur"]

    # static layers
    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if lay == "letterbox":
        hl = spec["headline"]
        im, _ = text_img(hl["lines"], st.get("head_font", "Pretendard-Black.otf"), hl.get("size", 82),
                         accent=tuple(st.get("accent", (255, 214, 64, 255))), gap=8, room=1000)
        static.alpha_composite(im, (0, int((by - im.height) / 2) + hl.get("dy", 10)))
        br = spec.get("brand")
        if br:
            im, _ = text_img([br["text"]], st.get("brand_font", "BlackHanSans-Regular.ttf"), br.get("size", 96), room=900)
            yb = by + bh + int((H - by - bh - im.height) / 2) - 20
            static.alpha_composite(im, (0, yb))
            if br.get("sub"):
                im2, _ = text_img([br["sub"]], st.get("small_font", "Pretendard-SemiBold.otf"), 34, fill=(255, 255, 255, 170))
                static.alpha_composite(im2, (0, yb + im.height - 40))
    # pre-render caption images
    caps = []
    for c in spec.get("subs", []):
        if lay == "letterbox":
            f = st.get("sub_font", "Pretendard-Bold.otf"); size = st.get("sub_size", 48)
            ti, _ = text_img(c["text"].split("\n"), f, size, gap=6, room=920)
            # rounded translucent box behind
            bb = ti.getbbox() or (0, 0, 10, 10)
            boxim = Image.new("RGBA", ti.size, (0, 0, 0, 0)); d = ImageDraw.Draw(boxim)
            d.rounded_rectangle((bb[0] - 26, bb[1] - 14, bb[2] + 26, bb[3] + 14), radius=22, fill=(0, 0, 0, 150))
            boxim.alpha_composite(ti); im = boxim
            y = by + bh - im.height - st.get("sub_margin", 18)
        else:
            f = st.get("sub_font", "Pretendard-Black.otf"); size = c.get("size", st.get("sub_size", 96))
            im, _ = text_img(c["text"].split("\n"), f, size, stroke=st.get("stroke", 7), gap=10, room=st.get("room", 980),
                             accent=tuple(st.get("accent", (255, 214, 64, 255))), shadow=st.get("shadow", .5))
            y = int(H * c.get("y", st.get("sub_y", .40))) - im.height // 2
        frames = None
        if lay != "letterbox" and st.get("word_reveal", False) and c.get("reveal", True):
            nw = sum(len([w for w in ln.replace("[", "").replace("]", "").split(" ") if w]) for ln in c["text"].split("\n"))
            if c.get("wt"): assert len(c["wt"]) == nw, (c["text"], len(c["wt"]), nw)
            if nw > 1:
                frames = [text_img(c["text"].split("\n"), f, size, stroke=st.get("stroke", 7), gap=10, room=st.get("room", 980),
                                   accent=tuple(st.get("accent", (255, 214, 64, 255))), shadow=st.get("shadow", .5), upto=k)[0]
                          for k in range(1, nw + 1)]
        caps.append((c["t0"], c["t1"], im, y, c.get("pop", True), frames, c.get("wt")))
    for t0, t1, im, y, *_ in caps:
        bb = im.getbbox()
        if bb and (y + bb[3] > H - 670 or y + bb[1] < 270):
            print(f"[safe-zone] caption {t0:.2f}-{t1:.2f}s spans y {y + bb[1]}..{y + bb[3]} (keep 270..{H - 670})")
    ovs = []
    for o in spec.get("overlays", []):
        if o["type"] == "arrow":
            im = arrow(o.get("len", 170)).rotate(o.get("angle", 0), expand=True, resample=Image.BICUBIC)
        elif o["type"] == "tag":
            im = pill(o["text"], st.get("tag_font", "Pretendard-Bold.otf"), o.get("size", 44), (255, 255, 255, 255),
                      tuple(o.get("bg", (230, 45, 45, 235))), radius=12)
        elif o["type"] == "badge":
            im = pill(o["text"], st.get("tag_font", "Pretendard-Bold.otf"), o.get("size", 40), (20, 20, 20, 255),
                      tuple(o.get("bg", (255, 255, 255, 230))))
        elif o["type"] == "image":
            im = Image.open(o["path"]).convert("RGBA")
        elif o["type"] == "ring":
            r = o.get("r", 150); wd = o.get("width", 10); im = Image.new("RGBA", (2 * r + 40, 2 * r + 40), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse((20, 20, 20 + 2 * r, 20 + 2 * r), outline=tuple(o.get("color", (235, 40, 40, 255))), width=wd)
            shd = im.getchannel("A").filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * .5))
            s_ = Image.new("RGBA", im.size, (0, 0, 0, 0)); s_.putalpha(shd); c_ = Image.new("RGBA", im.size, (0, 0, 0, 0))
            c_.alpha_composite(s_, (0, 3)); c_.alpha_composite(im); im = c_
            o.setdefault("x", int(o["cx"] - im.width / 2)); o.setdefault("y", int(o["cy"] - im.height / 2))
        elif o["type"] == "text":
            im, _ = text_img(o["text"].split("\n"), o.get("font", st.get("sub_font", "Pretendard-Black.otf")), o.get("size", 92),
                             stroke=o.get("stroke", st.get("stroke", 7)), gap=8, room=o.get("room", st.get("room", 800)),
                             accent=tuple(st.get("accent", (255, 214, 64, 255))), shadow=.55)
            o.setdefault("x", 0); o.setdefault("y", int(o.get("yc", .2) * H) - im.height // 2)
        elif o["type"] == "flash":
            im = Image.new("RGBA", (W, H), (255, 255, 255, 255)); o["x"] = 0; o["y"] = 0
        elif o["type"] == "counter":  # number counting up: {to, dur, prefix, suffix, size, yc}
            im = None
        elif o["type"] == "magnify":
            im = magnifier(o["src"], o["box"], o.get("r", 250), tuple(o.get("ring", (235, 40, 40, 255))))
            o.setdefault("x", int(o.get("cx", W / 2) - im.width / 2)); o.setdefault("y", int(o.get("cy", H * .72) - im.height / 2))
            if o.get("label"):
                lb = pill(o["label"], st.get("tag_font", "Pretendard-Black.otf"), o.get("label_size", 52), (255, 255, 255, 255),
                          tuple(o.get("ring", (235, 40, 40, 245))), radius=14)
                c = Image.new("RGBA", (max(im.width, lb.width), im.height + lb.height - 30), (0, 0, 0, 0))
                c.alpha_composite(im, ((c.width - im.width) // 2, 0)); c.alpha_composite(lb, ((c.width - lb.width) // 2, im.height - 30))
                o["x"] -= (c.width - im.width) // 2; im = c
        elif o["type"] == "endcard":
            lines = o["lines"]; im, _ = text_img(lines, st.get("end_font", st.get("sub_font", "Pretendard-Black.otf")), o.get("size", 100),
                                                 stroke=st.get("stroke", 7), accent=tuple(st.get("accent", (255, 214, 64, 255))),
                                                 shadow=.55, gap=14)
            if o.get("sub"):
                if o.get("sub_pill", True):
                    p2 = pill(o["sub"], st.get("small_font", "Pretendard-Bold.otf"), o.get("sub_size", 50), (255, 255, 255, 255),
                              (230, 45, 45, 240), padx=30, pady=12, radius=14)
                    s2 = Image.new("RGBA", (W, p2.height + 40), (0, 0, 0, 0)); s2.alpha_composite(p2, ((W - p2.width) // 2, 10))
                else:
                    s2, _ = text_img([o["sub"]], st.get("small_font", "Pretendard-SemiBold.otf"), o.get("sub_size", 46),
                                     stroke=4, shadow=.5)
                c = Image.new("RGBA", (W, im.height + s2.height - 20), (0, 0, 0, 0)); c.alpha_composite(im, (0, 0))
                c.alpha_composite(s2, (0, im.height - 20)); im = c
            if o.get("panel", True):  # dark band so the place name reads on any background
                bb = im.getbbox() or (0, 0, W, im.height)
                pnl = Image.new("RGBA", (W, im.height + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(pnl)
                d.rounded_rectangle((40, bb[1] + 10, W - 40, bb[3] + 70), radius=36, fill=(0, 0, 0, 150))
                pnl = pnl.filter(ImageFilter.GaussianBlur(2)); pnl.alpha_composite(im, (0, 40)); im = pnl
            o.setdefault("x", 0); o.setdefault("y", int(H * o.get("yc", .42)) - im.height // 2)
        ovs.append((o, im))

    for o, im in ovs:
        if im is None or o["type"] in ("flash", "image", "ring", "magnify", "arrow"): continue
        bb = im.getbbox()
        if bb and (o.get("y", 0) + bb[3] > H - 670 or o.get("y", 0) + bb[1] < 270):
            print(f"[safe-zone] {o['type']} '{str(o.get('text', o.get('lines', '')))[:16]}' {o['t0']:.2f}s spans y {o.get('y', 0) + bb[1]}..{o.get('y', 0) + bb[3]}")
    if os.environ.get("LINT_ONLY"): return None, total
    # gradient for full layout legibility
    grad = None
    if lay == "full" and st.get("vignette", .35):
        yy = np.linspace(0, 1, H)[:, None, None]
        g = st.get("vignette", .35)
        grad = (g * (np.abs(yy - .45) / .55) ** 1.6 + .06).astype(np.float32)

    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    vid = os.path.join(work, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "19", "-maxrate", "8M", "-bufsize", "16M", "-preset", "slow",
                            "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    cover = None; held = {}; _cnt = {}
    for i in range(N):
        raw = dec.stdout.read(bw * bh * 3)
        if len(raw) < bw * bh * 3: break
        tt = i / FPS
        fr = np.frombuffer(raw, np.uint8).reshape(bh, bw, 3)
        k = max(j for j in range(len(shot_starts)) if shot_starts[j] <= tt + 1e-6); lt = tt - shot_starts[k]
        sk = spec["shots"][k]
        fz = sk.get("freeze")  # hold the frame at local time `freeze` and fade to grey
        if fz is not None:
            if lt < fz or held.get(k) is None: held[k] = fr
            if lt >= fz:
                fr = held[k]; sat = 1 - min(1, (lt - fz) / .25) * (1 - sk.get("freeze_sat", .25))
                g = fr.astype(np.float32).mean(axis=2, keepdims=True); fr = (g + (fr - g) * sat).clip(0, 255).astype(np.uint8)
        z = 1 + .05 * (1 - ease(lt / .3)) if spec.get("punch", True) else 1
        if sk.get("zoom"):  # slow push-in [z0, z1] around (zx, zy)
            z0, z1 = sk["zoom"]; z *= z0 + (z1 - z0) * min(lt / sk["dur"], 1)
        img = Image.fromarray(fr)
        Tt = spec.get("trans_dur", .2); tmode = None
        nxt = spec["shots"][k + 1].get("trans") if k < len(spec["shots"]) - 1 else None
        rem = sk["dur"] - lt
        if nxt and rem < Tt: tmode, tp = nxt, 1 - rem / Tt
        elif k > 0 and sk.get("trans") and lt < Tt: tmode, tp = sk["trans"], 1 - lt / Tt
        if z > 1.001:
            cw, ch = int(bw / z), int(bh / z); zx, zy = sk.get("zx", .5), sk.get("zy", .5)
            x0 = int(min(max(zx * bw - cw / 2, 0), bw - cw)); y0 = int(min(max(zy * bh - ch / 2, 0), bh - ch))
            img = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((bw, bh), Image.BILINEAR)
        if grad is not None:
            a = np.asarray(img).astype(np.float32) * (1 - grad); img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        canvas.paste(img, (bx, by))
        canvas.alpha_composite(static)
        for o, im in ovs:
            if not (o["t0"] <= tt < o["t1"]): continue
            lt2 = tt - o["t0"]; a = 1.0 if o["t0"] <= 0 else ease(lt2 / .2)
            x, y = o.get("x", 0), o.get("y", 0)
            if o["type"] == "arrow":
                bob = 14 * math.sin(lt2 * 7)
                ang = math.radians(o.get("angle", 0)); x -= bob * math.cos(ang); y += bob * math.sin(ang)
            if o["type"] == "endcard": y += int((1 - a) * 30)
            if o.get("slam"):  # hard slam: full opacity, scale 1.6 -> 1.0 over 5 frames
                a = 1.0; sc = 1 + .6 * (1 - ease(lt2 / (5 / FPS)))
                if sc > 1.001:
                    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
                    x -= (im.width - im.width / sc) / 2; y -= (im.height - im.height / sc) / 2
            if o["type"] == "flash": a = max(0.0, 1 - lt2 / max(o["t1"] - o["t0"], .01)) * o.get("peak", .85)
            if o["type"] == "counter":
                v = int(round(o["to"] * (1 - (1 - min(lt2 / o.get("dur", 1.6), 1)) ** 3)))
                s_ = o.get("prefix", "") + f"{v:,}" + (o.get("suffix", "") if v >= o["to"] else "")
                key = ("cnt", s_)
                if key not in _cnt:
                    _cnt[key], _ = text_img([s_], o.get("font", st.get("sub_font", "Pretendard-Black.otf")), o.get("size", 170),
                                            fill=tuple(o.get("color", (255, 214, 64, 255))), stroke=o.get("stroke", 10), shadow=.6, room=1000)
                im = _cnt[key]; x = 0; y = int(o.get("yc", .55) * H) - im.height // 2; a = 1.0
            paste(canvas, im, x, y, alpha=a)
        for t0, t1, im, y, pop, frames, wt in caps:
            if t0 <= tt < t1:
                lt3 = tt - t0
                if frames and wt:  # word k appears when it is spoken (wt = absolute times per word)
                    kk = sum(1 for w in wt if w <= tt + 1e-6)
                    if kk < len(wt): im = frames[max(kk, 1) - 1]
                elif frames:  # fallback: reveal across the first 55% of the caption (max 1.4s)
                    span = min((t1 - t0) * .55, 1.4)
                    if lt3 < span: im = frames[min(len(frames) - 1, int(lt3 / max(span, .01) * len(frames)))]
                if pop and lt3 < .14:
                    s = .9 + .1 * ease(lt3 / .14)
                    im2 = im.resize((int(im.width * s), int(im.height * s)), Image.BICUBIC)
                    canvas.alpha_composite(im2, (int((W - im2.width) / 2), int(y + (im.height - im2.height) / 2)))
                else:
                    canvas.alpha_composite(im, (0, y))
        if tmode: canvas = trans_fx(canvas.convert("RGB"), tmode, tp, W, H).convert("RGBA")
        out = np.asarray(canvas.convert("RGB"))
        if i == 0: first = out.copy()
        Lt = spec.get("loop_tail", 0)
        if Lt and tt > total - Lt:  # dissolve into frame 0 -> seamless replay
            a_ = ease((tt - (total - Lt)) / Lt)
            out = (out.astype(np.float32) * (1 - a_) + first.astype(np.float32) * a_).astype(np.uint8)
        if i == int(spec.get("cover_t", 1.0) * FPS): cover = out.copy()
        enc.stdin.write(out.tobytes())
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill(); dec.wait()

    au = spec.get("audio", {}); out = spec["out"]
    ins = ["-i", vid]; fc = []; n = 1
    if au.get("music"):
        ins += ["-ss", str(au.get("music_ss", 0)), "-i", au["music"]]
        duck = ""
        for d_ in au.get("duck", []):  # [a, b, v(, ramp)]: smooth dip to v between a..b, ramps in/out
            a, b_, v = d_[:3]; r = d_[3] if len(d_) > 3 else .15
            ex = (f"if(lt(t\\,{a - r})\\,1\\,if(lt(t\\,{a})\\,1-(1-{v})*(t-{a - r})/{r}\\,if(lt(t\\,{b_})\\,{v}\\,"
                  f"if(lt(t\\,{b_ + r})\\,{v}+(1-{v})*(t-{b_})/{r}\\,1))))")
            duck += f",volume=eval=frame:volume='{ex}'"
        fc.append(f"[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={au.get('music_vol', .22)}{duck},afade=t=in:d=0.3,afade=t=out:st={total - 1:.3f}:d=1[m]"); n += 1
    if au.get("voice"):
        d = int(au.get("voice_delay", .2) * 1000)
        ins += ["-ss", str(au.get("voice_ss", 0)), "-i", au["voice"]]; fc.append(f"[{n}:a]adelay={d}|{d},volume=1.0[v]"); n += 1
    labels = []
    sfx_list = list(au.get("sfx", []))
    if au.get("whoosh"):
        for kk, cst in enumerate(shot_starts[1:], start=1):
            if spec["shots"][kk].get("trans"):
                sfx_list.append({"path": au["whoosh"], "t": max(0, cst - .15), "dur": .5, "vol": au.get("whoosh_vol", .15), "fo": .2})
    if au.get("hit"):
        for kk, cst in enumerate(shot_starts[1:], start=1):
            if spec["shots"][kk].get("hit"):
                sfx_list.append({"path": au["hit"], "t": max(0, cst - .02), "dur": 1.2, "vol": au.get("hit_vol", .5), "fo": .3})
    for j, sx in enumerate(sfx_list):  # extra sounds: {path, t, ss, dur, vol}
        d = int(sx["t"] * 1000)
        ins += ["-ss", str(sx.get("ss", 0)), "-t", str(sx.get("dur", 3)), "-i", sx["path"]]
        vol = sx.get("vol", .6)
        if sx.get("env"):  # [[local_t, gain], ...] linear envelope, multiplied by vol
            pts = sx["env"]; ex = f"{pts[-1][1]}"
            for (ta, ga), (tb, gb) in reversed(list(zip(pts, pts[1:]))):
                ex = f"if(lt(t\\,{tb})\\,{ga}+({gb}-{ga})*(t-{ta})/{max(tb - ta, 1e-3)}\\,{ex})"
            ex = f"if(lt(t\\,{pts[0][0]})\\,{pts[0][1]}\\,{ex})"
            volf = f"volume={vol},volume=eval=frame:volume='{ex}'"
        else:
            volf = f"volume={vol}"
        fo = sx.get("fo", .4)
        fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,afade=t=in:d=0.15,afade=t=out:st={max(sx.get('dur', 3) - fo, 0):.2f}:d={fo},"
                  f"{volf},adelay={d}|{d}[x{j}]"); n += 1; labels.append(f"[x{j}]")
    if fc:
        srcs = ("[m]" if au.get("music") else "") + ("[v]" if au.get("voice") else "") + "".join(labels)
        cnt = srcs.count("[")
        mix = f"{srcs}amix=inputs={cnt}:duration=longest:normalize=0,atrim=0:{total:.3f}" if cnt > 1 else f"{srcs}anull"
        fc.append(mix + ",loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", vid, "-c", "copy", out])
    if cover is not None and spec.get("cover"): Image.fromarray(cover).save(spec["cover"], quality=92)
    print("wrote", out, f"{total:.1f}s", os.path.getsize(out) // 1024, "KB")
    return out, total


def sheet(out, times, path):
    ims = []
    for k, t in enumerate(times):
        p = f"/tmp/_s{k}.jpg"
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", p]); ims.append(Image.open(p).resize((360, 640)))
    S = Image.new("RGB", (360 * len(ims), 640))
    for k, im in enumerate(ims): S.paste(im, (360 * k, 0))
    S.save(path, quality=85); print("sheet", path)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    o, tot = render(spec)
    if "--sheet" in sys.argv:
        sheet(o, spec.get("sheet_t", [0.8, tot * .25, tot * .45, tot * .65, tot - 1.2]), os.path.splitext(o)[0] + "_sheet.jpg")
