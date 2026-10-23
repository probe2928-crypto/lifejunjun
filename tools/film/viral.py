#!/usr/bin/env python3
"""인생준준 viral listicle reel — native Reels look (not 'cinematic AI').

usage: python3 tools/film/viral.py tools/film/specs/viralNN.json [--preview]

Grammar taken from high-view travel reels: text hook + bass hit on frame 1 (no logo intro),
countdown list (save/send-worthy info), bold Korean sans captions in the upper third,
fast punch-in on every cut, whip-pan transitions with motion blur + whoosh, 120 BPM beat,
1-beat silence before #1, CTA that asks people to SEND it, ending that loops to the start.

Typography follows the 인생준준 homepage: Noto Serif KR Black titles, Noto Sans KR body,
IBM Plex Mono labels (tools/film/fonts), seal red #C8261C accents, soft shadows, no outlines.

spec: {"id","out","bpm":120,
       "hook": {"img","kb":[s0,s1,cx,cy], "kicker":"LIFEJUNJUN · RUN & TREK · TOP 5",
                "title":"line1\nline2", "sub":"red pill text", "beats":4},
       "items":[{"rank":5,"img","kb":[s0,s1,cx,cy],"name":"한글 이름","place":"나라 도시",
                 "en":"City, Country","fact":"red pill fact","meta":"10 KM  ·  +300 M","beats":5}, …],
       "cta": {"img","kb":[…],"line1":"serif line(\n ok)","line2":"sans line","beats":6},
       "caption":"…", "link": "optional site link for the caption/comment"}
kb: s0 = start zoom (punch-in from), s1 = settle zoom (≥1), cx/cy = subject position 0..1 in the photo.
"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W, H, FPS = 1080, 1920, 30
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SERIF_K = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"      # = Noto Serif KR 900 (homepage h1)
SERIF_SB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
MONO = os.path.join(FDIR, "IBMPlexMono-Medium.ttf")                    # homepage mono labels
MONO_SB = os.path.join(FDIR, "IBMPlexMono-SemiBold.ttf")
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"

def font(p, s): return ImageFont.truetype(p, s, index=1) if p.endswith(".ttc") else ImageFont.truetype(p, s)

def ease(x): x = min(max(x, 0.), 1.); return x * x * (3 - 2 * x)
def eout(x): x = min(max(x, 0.), 1.); return 1 - (1 - x) ** 3

def text_img(lines, maxw=980):
    """lines: [(text, fontpath, size, fill, stroke)] stacked & centred, returns RGBA float."""
    rend = []
    for txt, fp, sz, fill, stroke in lines:
        f = font(fp, sz)
        bb = f.getbbox(txt, stroke_width=stroke)
        rend.append((txt, f, fill, stroke, bb, sz))
    gap = 14
    tw = max(bb[2] - bb[0] for *_, bb, _ in rend) + 40
    th = sum(bb[3] - bb[1] for *_, bb, _ in rend) + gap * (len(rend) - 1) + 40
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im); y = 20
    for txt, f, fill, stroke, bb, sz in rend:
        w = bb[2] - bb[0]; x = (tw - w) / 2 - bb[0]
        d.text((x, y - bb[1]), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += bb[3] - bb[1] + gap
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * .55))
    out = Image.alpha_composite(sh, im)
    if out.width > maxw:
        k = maxw / out.width; out = out.resize((maxw, int(out.height * k)), Image.LANCZOS)
    return np.asarray(out).astype(np.float32) / 255


def tline(txt, fp, size, fill=(255, 255, 255, 255), track=0.0):
    """one line with letter-spacing, soft editorial shadow (no outline)."""
    f = font(fp, size); sp = size * track
    ws = [f.getlength(c) for c in txt]; asc, desc = f.getmetrics()
    tw = int(sum(ws) + sp * max(len(txt) - 1, 0)) + 60; th = asc + desc + 60
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 30
    for c, w in zip(txt, ws):
        d.text((x, 30), c, font=f, fill=fill); x += w + sp
    a = im.getchannel("A")
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(max(6, size * .16))).point(lambda v: min(255, v * .75)))
    sh2 = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh2.putalpha(a.filter(ImageFilter.GaussianBlur(2)).point(lambda v: v * .35))
    out = Image.alpha_composite(Image.alpha_composite(sh, sh2), im)
    return np.asarray(out).astype(np.float32) / 255

def pill(txt, fp, size, bg=(200, 38, 28), fg=(255, 255, 255, 255), track=.08, padx=26, pady=14):
    f = font(fp, size); sp = size * track; ws = [f.getlength(c) for c in txt]
    bb = f.getbbox("Hg가"); tw = int(sum(ws) + sp * max(len(txt) - 1, 0)); th = bb[3] - bb[1]
    im = Image.new("RGBA", (tw + 2 * padx, th + 2 * pady), bg + (255,)); d = ImageDraw.Draw(im); x = padx
    for c, w in zip(txt, ws):
        d.text((x, pady - bb[1]), c, font=f, fill=fg); x += w + sp
    return np.asarray(im).astype(np.float32) / 255

def fit(L, maxw=990):
    if L.shape[1] <= maxw: return L
    k = maxw / L.shape[1]; im = Image.fromarray((L * 255).astype(np.uint8))
    return np.asarray(im.resize((maxw, int(L.shape[0] * k)), Image.LANCZOS)).astype(np.float32) / 255

def rule(w=120, h=4, col=(200, 38, 28)):
    a = np.zeros((h, w, 4), np.float32); a[..., :3] = np.array(col) / 255; a[..., 3] = 1; return a

def seal(px):
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, px - 1, px - 1), radius=int(px * .1), fill=(200, 38, 28, 255))
    f = font(SERIF_B, int(px * .36))
    for k, l in enumerate(["인생", "준준"]):
        d.text(((px - f.getlength(l)) / 2, px * (.12 + k * .40)), l, font=f, fill="white")
    return np.asarray(im).astype(np.float32) / 255

def place(fr, L, cx, cy, al=1.0, sc=1.0):
    if al <= .003: return
    if abs(sc - 1) > .002:
        h0, w0 = L.shape[:2]
        L = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).resize((max(1, int(w0 * sc)), max(1, int(h0 * sc))), Image.BICUBIC)).astype(np.float32) / 255
    lh, lw = L.shape[:2]; x = int(cx * W - lw / 2); y = int(cy * H - lh / 2)
    sub = L[max(0, -y):min(lh, H - y), max(0, -x):min(lw, W - x)]; y0, x0 = max(y, 0), max(x, 0)
    A = sub[..., 3:4] * min(al, 1)
    fr[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = fr[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] * (1 - A) + sub[..., :3] * A

def hblur(a, k):
    k = int(k)
    if k < 2: return a
    c = np.cumsum(np.pad(a, ((0, 0), (k, k), (0, 0)), mode="edge"), axis=1)
    return (c[:, 2 * k:] - c[:, :-2 * k])[:, :W] / (2 * k)

class Reel:
    def __init__(self, spec):
        self.spec = spec; self.B = 60 / spec.get("bpm", 120)
        segs = [dict(spec["hook"], kind="hook")] + [dict(it, kind="item") for it in spec["items"]] + [dict(spec["cta"], kind="cta")]
        t = 0.
        for s in segs:
            s["dur"] = s.get("beats", 5) * self.B; s["start"] = t; t += s["dur"]
            im = Image.open(os.path.join(ROOT, s["img"])).convert("RGB")
            if max(im.size) < 2400:
                k = 2400 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            im = ImageEnhance.Color(im).enhance(1.18); im = ImageEnhance.Contrast(im).enhance(1.07)
            s["_im"] = im.filter(ImageFilter.UnsharpMask(2, 80, 2))
            n = len(spec["items"])
            if s["kind"] == "hook":
                s["_kick"] = tline(s.get("kicker", "LIFEJUNJUN  ·  RUN & TREK"), MONO, 26, (255, 255, 255, 230), .32)
                s["_title"] = [fit(tline(l, SERIF_K, 116, track=-.01)) for l in s["title"].split("\n")]
                s["_sub"] = pill(s["sub"], SANS_B, 40, track=.02) if s.get("sub") else None
            elif s["kind"] == "item":
                s["_kick"] = tline(f"N° {s['rank']:02d} / {n:02d}   —   {s.get('en', '').upper()}", MONO, 26, (255, 255, 255, 235), .28)
                s["_num"] = tline(f"{s['rank']:02d}", SERIF_K, 210, (255, 255, 255, 255), -.02)
                s["_name"] = fit(tline(s["name"], SERIF_K, 96, track=-.01))
                s["_place"] = tline(s["place"], SANS_M, 40, (255, 255, 255, 235), .04)
                s["_fact"] = pill(s["fact"], SANS_B, 38, track=.02)
                s["_meta"] = tline(s.get("meta", ""), MONO, 24, (255, 255, 255, 220), .22) if s.get("meta") else None
            else:
                s["_title"] = [fit(tline(l, SERIF_K, 92, track=-.01)) for l in s["line1"].split("\n")]
                s["_sub"] = tline(s["line2"], SANS_M, 44, (255, 255, 255, 240), .03)
                s["_brand"] = tline("LIFEJUNJUN  ·  @lifejunjun", MONO, 26, (255, 255, 255, 230), .3)
                s["_brand2"] = tline("여백의 지도에서 더 보기 — 프로필 링크", SANS_M, 32, (255, 255, 255, 230), .03)
        self.S = segs; self.T = t; self.SEAL = seal(84); self.SEAL_BIG = seal(150); self.RULE = rule()
        self.CUTS = [s["start"] for s in segs[1:]]
        yy = np.mgrid[0:H, 0:W][0].astype(np.float32) / H
        self.TOPSHADE = (1 - .5 * np.clip((.45 - yy) / .45, 0, 1) ** 1.3 - .25 * np.clip((yy - .82) / .18, 0, 1))[..., None]

    def shot(self, s, lt):
        im = s["_im"]; iw, ih = im.size; s0, s1, cx, cy = s["kb"]
        p = lt / s["dur"]
        sc = s1 + (s0 - s1) * (1 - eout(lt / .55)) * 1.0 + (-.04 * p)  # fast punch-in then slow drift
        z = max(W / iw, H / ih) * max(sc, 1.0); vw, vh = W / z, H / z
        x0 = min(max(cx * iw - vw / 2, 0), iw - vw); y0 = min(max(cy * ih - vh / 2, 0), ih - vh)
        a = np.asarray(im.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), resample=Image.BILINEAR)).astype(np.float32) / 255
        return a * self.TOPSHADE

    def overlay(self, f, s, lt):
        k = s["kind"]
        up = lambda d, dur=.35: (ease((lt - d) / dur), (1 - eout((lt - d) / dur)) * .012)   # (alpha, rise)
        if k == "hook":
            a, r = up(0, .2); place(f, s["_kick"], .5, .135 + r, a)
            place(f, self.RULE, .5, .165, ease(lt / .3))
            for j, L in enumerate(s["_title"]):
                a, r = up(.05 + j * .08, .3); place(f, L, .5, .215 + j * .062 + r, a)
            if s["_sub"] is not None:
                a, r = up(.35, .25); place(f, s["_sub"], .5, .215 + len(s["_title"]) * .062 + .02 + r, a)
        elif k == "item":
            a, r = up(0, .2); place(f, s["_kick"], .5, .085 + r, a)
            a, r = up(0, .25); place(f, s["_num"], .5, .155 + r, a, 1 + .06 * (1 - eout(lt / .3)))
            place(f, self.RULE, .5, .208, ease((lt - .1) / .3))
            a, r = up(.12, .3); place(f, s["_name"], .5, .25 + r, a)
            a, r = up(.25, .3); place(f, s["_place"], .5, .292 + r, a)
            a, r = up(.5, .25); place(f, s["_fact"], .5, .337 + r, a)
            if s["_meta"] is not None:
                a, r = up(.7, .3); place(f, s["_meta"], .5, .375 + r, a)
            place(f, self.SEAL, .085, .05, .95)
        else:
            for j, L in enumerate(s["_title"]):
                a, r = up(j * .08, .3); place(f, L, .5, .235 + j * .055 + r, a)
            a, r = up(.25, .3); place(f, s["_sub"], .5, .235 + len(s["_title"]) * .055 + .015 + r, a)
            if lt > .6:
                place(f, self.SEAL_BIG, .5, .56, min(1, (lt - .6) / .06), 1 + .25 * (1 - eout((lt - .6) / .15)))
                place(f, s["_brand"], .5, .64, ease((lt - .9) / .3))
                place(f, s["_brand2"], .5, .672, ease((lt - 1.1) / .3))

    def render_seg(self, i, t):
        s = self.S[i]; lt = min(max(t - s["start"], 0), s["dur"] - 1e-3)
        f = self.shot(s, lt); self.overlay(f, s, lt); return f

    def frame(self, t):
        WH = .12  # whip half-duration
        i = max(j for j, s in enumerate(self.S) if s["start"] <= t) if t < self.T else len(self.S) - 1
        s = self.S[i]; lt = t - s["start"]
        # find a cut within the whip window
        cut = None
        if i < len(self.S) - 1 and s["dur"] - lt < WH: cut = i + 1
        elif i > 0 and lt < WH: cut = i
        if cut is None:
            f = self.render_seg(i, t)
        else:
            c = self.S[cut]["start"]; q = (t - (c - WH)) / (2 * WH)   # 0..1 across the whip
            off = int(ease(q) * W)
            a = self.render_seg(cut - 1, t); b = self.render_seg(cut, t)
            f = np.concatenate([a, b], axis=1)[:, off:off + W]
            speed = np.sin(np.pi * q)                                   # fastest mid-whip
            f = hblur(f, 4 + speed * 90)
        if s["kind"] == "hook" and lt < .1: f = f + (1 - lt / .1) * .35
        if s.get("rank") == 1 and lt < .1: f = f + (1 - lt / .1) * .5
        return np.clip(f, 0, 1)

    def audio(self, path):
        sr = 48000; B = self.B; n = int(self.T * sr) + 1; tt = np.arange(n) / sr; rng = np.random.default_rng(3)
        sig = np.zeros(n)
        def add(t0, x, g=1.):
            i0 = int(t0 * sr)
            if 0 <= i0 < n: L = min(len(x), n - i0); sig[i0:i0 + L] += x[:L] * g
        lp = lambda x, k: np.convolve(x, np.ones(k) / k, mode="same")
        def kick(g=1., L=.4):
            tl = np.arange(int(L * sr)) / sr
            return (np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-tl * 38)) / sr) * np.exp(-tl * 8) + rng.normal(0, 1, len(tl)) * np.exp(-tl * 300) * .25) * g
        def clap():
            L = int(.18 * sr); tl = np.arange(L) / sr; x = rng.normal(0, 1, L)
            x = x - lp(x, 8); return x * (np.exp(-tl * 30) + .5 * np.exp(-np.abs(tl - .012) * 400)) * .45
        def hat(open_=False):
            L = int((.14 if open_ else .05) * sr); x = np.diff(rng.normal(0, 1, L), prepend=0)
            return x * np.exp(-np.arange(L) / sr * (25 if open_ else 80)) * .16
        def whoosh(L=.32):
            N = int(L * sr); tl = np.arange(N) / sr; x = rng.normal(0, 1, N)
            env = np.sin(np.pi * tl / L) ** 2; out = np.zeros(N)
            for k0 in range(0, N, 480):  # sweeping lowpass
                k = max(2, int(40 - 36 * (k0 / N))); out[k0:k0 + 480] = lp(x[max(0, k0 - 200):k0 + 680], k)[min(200, k0):min(200, k0) + len(out[k0:k0 + 480])]
            return out * env * .9
        one = next(s for s in self.S if s.get("rank") == 1)["start"]
        roots = [55, 55, 65.4, 49]  # A A C G bass line, 2 bars each
        # hook: pattern interrupt — sub drop on frame 1
        L = int(1.6 * sr); tl = np.arange(L) / sr
        add(0, np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tl * 4)) / sr) * np.exp(-tl * 1.6) * 1.2 + kick(1.3, 1.6))
        t = 0.; bi = 0
        while t < self.T - 1e-6:
            silent = one - B <= t < one
            if not silent:
                if bi % 1 == 0: add(t, kick(1.0 if t >= 2 * B else .0))
                if bi % 2 == 1: add(t, clap())
                add(t + B / 2, hat(open_=(bi % 4 == 3)))
                add(t + B / 4, hat(), .5); add(t + 3 * B / 4, hat(), .5)
                r = roots[(bi // 8) % 4]; Lb = int(B * .92 * sr); tb = np.arange(Lb) / sr
                bass = (np.sin(2 * np.pi * r * tb) + .35 * np.sin(2 * np.pi * 2 * r * tb)) * (1 - np.exp(-tb * 60)) * np.exp(-tb * 2.2)
                add(t, bass, .55)
            t += B; bi += 1
        for c in self.CUTS: add(c - .16, whoosh())
        # riser into #1 + big hit
        L = int(2 * B * sr); tl = np.arange(L) / sr; x = rng.normal(0, 1, L); x = x - lp(x, 30)
        add(one - 3 * B, x * (tl / tl[-1]) ** 2.5 * .5)
        sig[int((one - B * .5) * sr):int(one * sr)] *= .0
        L = int(2.2 * sr); tl = np.arange(L) / sr
        add(one, np.sin(2 * np.pi * np.cumsum(28 + 80 * np.exp(-tl * 5)) / sr) * np.exp(-tl * 1.3) * 1.3 + kick(1.4, 2.2) + lp(rng.normal(0, 1, L), 4) * np.exp(-tl * 7) * .6)
        # pad (sidechained) for body
        pad = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(220, .05), (261.6, .04), (329.6, .04), (440, .02)])
        duck = np.ones(n)
        for k in np.arange(0, self.T, B):
            i0 = int(k * sr); L = min(int(B * sr), n - i0); duck[i0:i0 + L] = .25 + .75 * (1 - np.exp(-np.arange(L) / sr * 9))
        sig += pad * duck
        cta = self.S[-1]["start"]; L = int(1.5 * sr); tl = np.arange(L) / sr
        add(cta + .5, sum(np.sin(2 * np.pi * f * tl) * a for f, a in [(523.3, .16), (784, .08), (1046, .05)]) * np.exp(-tl * 3) + kick(1.1, 1.5))
        irL = int(1.2 * sr); ir = rng.normal(0, 1, irL) * np.exp(-np.arange(irL) / sr * 5); ir /= np.sqrt((ir ** 2).sum())
        N = 1 << int(np.ceil(np.log2(n + irL))); wet = np.fft.irfft(np.fft.rfft(sig, N) * np.fft.rfft(ir, N), N)[:n]
        mix = sig + wet * .18; mix = np.tanh(mix / np.abs(mix).max() * 3.0); mix = mix / np.abs(mix).max() * .95
        mix *= np.clip((self.T - tt) / .08, 0, 1)
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.stack([mix, np.roll(mix, 160)], 1) * 32767).astype(np.int16).tobytes())

    def write(self, out):
        wav = out + ".wav"; self.audio(wav); nf = int(self.T * FPS)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-i", wav, "-c:v", "libx264", "-preset", "slow", "-b:v", "11M", "-maxrate", "15M", "-bufsize", "22M", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
        for i in range(nf):
            ff.stdin.write((self.frame(i / FPS) * 255).astype(np.uint8).tobytes())
            if i % 90 == 0: print(f"{i}/{nf}", flush=True)
        ff.stdin.close(); ff.wait(); os.remove(wav)

    def preview(self, path):
        ts = [.4] + [s["start"] + s["dur"] * .5 for s in self.S[1:]]
        ims = [Image.fromarray((self.frame(t) * 255).astype(np.uint8)).resize((360, 640)) for t in ts]
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims): sheet.paste(im, (k * 360, 0))
        sheet.save(path, quality=85); return path

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8")); r = Reel(spec)
    print(f"{spec['id']}: {r.T:.1f}s")
    if "--preview" in sys.argv:
        print(r.preview(os.path.join(ROOT, "tools", "film", "_preview_" + spec["id"] + ".jpg")))
    else:
        out = os.path.join(ROOT, spec["out"]); r.write(out); print("wrote", out)
