#!/usr/bin/env python3
"""인생준준 film engine — turns a JSON spec + still photos into a 1080x1920 cinematic reel.

usage:  python3 tools/film/engine.py tools/film/specs/film03.json [--preview]

Look: adidas-Originals / luxury-house grammar — macro push-ins, shallow depth of field with
rack focus, filmic grade (warm | mono | mono2color), halation, grain, beat-locked hard cuts,
punch words, a riser + silence + impact into the final wide shot, and the 인생준준 red seal
stamped at the end. Sound is synthesised (no licensed music needed).

spec:
{
  "id": "film-03-ascent", "title": "Ascent", "out": "media/film03-ascent.mp4",
  "bpm": 96, "grade": "warm" | "mono" | "mono2color",
  "shots": [ {"img": "media/photos/tmb-0.jpg", "beats": 4,
              "kb": [scale0, scale1, cx0, cx1, cy0, cy1],      # crop centre 0..1, scale ≥1
              "focus": [y0, y1], "dof": 16, "band": 0.16,       # optional, dof 0 = all sharp
              "word": "RUN.",                                   # optional punch word (centre)
              "line": "Before the first step",                  # optional serif italic line
              "ko": "한국어 한 줄",                                # optional Korean line
              "corner": ["CHAMONIX", "FRANCE"] } ...],          # optional corner labels
  "final": {"img": "...", "seconds": 6.6, "kb": [...], "line": "Every road has a history."},
  "caption": "instagram caption"
}
"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W, H, FPS = 1080, 1920, 24

def _f(*cands):
    for c in cands:
        if os.path.exists(c): return c
    return cands[-1]
F_SERIF_I = _f("/usr/share/texmf/fonts/opentype/public/lm/lmroman10-italic.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf")
F_MED = _f("/usr/share/fonts/opentype/inter/Inter-Medium.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
F_BLACK = _f("/usr/share/fonts/opentype/inter/Inter-Black.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
F_KO = _f("/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
F_KO_BLACK = _f("/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

def font(p, s):
    return ImageFont.truetype(p, s, index=1) if p.endswith(".ttc") else ImageFont.truetype(p, s)

def text_layer(txt, fp, size, track=0.0, alpha=1.0, shadow=0.5):
    f = font(fp, size); ws = [f.getlength(c) for c in txt]; sp = size * track
    tw = int(sum(ws) + sp * max(len(txt) - 1, 0)) + 40; a, d = f.getmetrics(); th = a + d + 40
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); x = 20
    for c, w in zip(txt, ws):
        dr.text((x, 20), c, font=f, fill=(255, 250, 240, int(255 * alpha))); x += w + sp
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(size * .25)).point(lambda v: v * shadow))
    return np.asarray(Image.alpha_composite(sh, im)).astype(np.float32) / 255

def make_seal(px):
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, px - 1, px - 1), radius=int(px * .09), fill=(200, 38, 28, 255))
    f = font(F_KO_BLACK, int(px * .36))
    for k, line in enumerate(["인생", "준준"]):
        d.text(((px - f.getlength(line)) / 2, px * (.12 + k * .40)), line, font=f, fill=(255, 255, 255, 255))
    a = np.asarray(im).astype(np.float32) / 255
    n = np.asarray(Image.fromarray((np.random.default_rng(4).random((px // 3 + 1, px // 3 + 1)) * 255).astype(np.uint8)).resize((px, px), Image.BILINEAR)).astype(np.float32) / 255
    a[..., 3] *= np.clip(.8 + n * .4, 0, 1)
    return a

def ease(x):
    x = min(max(x, 0.), 1.); return x * x * (3 - 2 * x)

class Film:
    def __init__(self, spec):
        self.spec = spec; self.B = 60.0 / spec.get("bpm", 96); self.grade_mode = spec.get("grade", "warm")
        self.S = []; t = 0.0
        for sh in spec["shots"]:
            d = dict(sh); d["dur"] = sh.get("beats", 3) * self.B; d["start"] = t; t += d["dur"]; self.S.append(d)
        fin = dict(spec["final"]); fin["dur"] = fin.get("seconds", 6.6); fin["start"] = t; fin["final"] = True
        fin.setdefault("dof", 0); self.S.append(fin); t += fin["dur"]
        self.TOTAL = t; self.STAMP = fin.get("stamp", 3.0)
        self.CUTS = [s["start"] for s in self.S[1:]]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); self.yn = yy / H; xn = xx / W
        r = np.sqrt(((xn - .5) * 2) ** 2 * .7 + ((self.yn - .5) * 2) ** 2)
        self.VIG = (1 - .5 * np.clip(r - .45, 0, 1) ** 1.5)[..., None]
        self.SCRIM = (1 - .58 * np.clip((self.yn - .64) / .3, 0, 1) ** 1.2 - .3 * np.clip((.12 - self.yn) / .12, 0, 1))[..., None]
        rng = np.random.default_rng(11)
        self.GR = [np.asarray(Image.fromarray(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)).resize((W, H), Image.BILINEAR))[..., None] for _ in range(6)]
        self.SRC = {}
        for s in self.S:
            p = os.path.join(ROOT, s["img"])
            if p not in self.SRC:
                im = Image.open(p).convert("RGB")
                if max(im.size) < 2600:
                    k = 2600 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
                self.SRC[p] = {"sharp": im}
            s["_p"] = p; s.setdefault("kb", [1.25, 1.08, .5, .5, .5, .5]); s.setdefault("focus", [.5, .5]); s.setdefault("band", .16)
            s.setdefault("dof", 14)
            if s["dof"] and s["dof"] not in self.SRC[p]:
                im = self.SRC[p]["sharp"]; z = max(W / im.width, H / im.height) * (s["kb"][0] + s["kb"][1]) / 2
                self.SRC[p][s["dof"]] = im.filter(ImageFilter.GaussianBlur(s["dof"] / z))
            s["_texts"] = []
            if s.get("word"): s["_texts"].append(("word", text_layer(s["word"], F_BLACK, 200, -.02, 1.0, .6), .5, .5, 0.0, s["dur"], 0, 0))
            if s.get("line"):
                end = self.STAMP - .25 if s.get("final") else s["dur"] - .1
                s["_texts"].append(("line", text_layer(s["line"], F_SERIF_I, 66 if s.get("final") else 92), .5, .78, .3, end, .8, .35))
            if s.get("ko"): s["_texts"].append(("ko", text_layer(s["ko"], F_KO, 40, .04, .95), .5, .835, .55, s["dur"] - .1, .8, .3))
            if s.get("corner"):
                s["_texts"].append(("cl", text_layer(s["corner"][0].upper(), F_MED, 22, .3, .85, .3), .0, .055, .25, s["dur"] - .1, .5, .3))
                s["_texts"].append(("cr", text_layer(s["corner"][1].upper(), F_MED, 22, .3, .85, .3), 1.0, .055, .25, s["dur"] - .1, .5, .3))
        self.SEAL = make_seal(300); self.MINI = make_seal(84)
        self.WORD = text_layer("인생준준", F_KO_BLACK, 104, .06)
        self.TAG2 = text_layer(spec.get("tag_ko", "함께 달리고, 함께 걷는 역사 여행"), F_KO, 34, .04, .9)
        self.TAG1 = text_layer("LIFE JUNJUN  ·  TRAVELLING THROUGH TIME", F_MED, 22, .32, .85)

    # ---- picture ----
    def grade(self, a, s, p):
        lum = (a @ np.array([.2126, .7152, .0722], np.float32))[..., None]
        mode = s.get("grade", self.grade_mode)
        if mode == "mono2color":
            mono = 1 - ease((p - .15) / .6) if s.get("final") or s.get("bloom") else 1.0
        else:
            mono = 1.0 if mode == "mono" else 0.0
        if mono < 1:
            c = lum + (a - lum) * .78
            sh = np.array([.86, .97, 1.04], np.float32); hi = np.array([1.10, 1.0, .82], np.float32)
            c = c * (sh + (hi - sh) * np.clip(lum * 1.3, 0, 1))
        else:
            c = a
        if mono > 0:
            bw = lum * np.array([1.0, .985, .955], np.float32)
            c = c * (1 - mono) + bw * mono
        c = np.clip((c - .5) * 1.14 + .5, 0, 1)
        return .045 + c * .9

    def render(self, s, lt):
        p = lt / s["dur"]; e = ease(p) * .6 + p * .4
        s0, s1, cx0, cx1, cy0, cy1 = s["kb"]
        sc = s0 + (s1 - s0) * e; cx = cx0 + (cx1 - cx0) * e; cy = cy0 + (cy1 - cy0) * e
        src = self.SRC[s["_p"]]; im = src["sharp"]; iw, ih = im.size
        z = max(W / iw, H / ih) * sc; vw, vh = W / z, H / z
        x0 = min(max(cx * iw - vw / 2, 0), iw - vw); y0 = min(max(cy * ih - vh / 2, 0), ih - vh)
        A = (1 / z, 0, x0, 0, 1 / z, y0)
        a = np.asarray(im.transform((W, H), Image.AFFINE, A, resample=Image.BICUBIC)).astype(np.float32) / 255
        if s["dof"]:
            b = np.asarray(src[s["dof"]].transform((W, H), Image.AFFINE, A, resample=Image.BILINEAR)).astype(np.float32) / 255
            f0, f1 = s["focus"]; fc = f0 + (f1 - f0) * ease((p - .1) / .7)
            m = np.clip((np.abs(self.yn - fc) - s["band"] / 2) / .22, 0, 1)[..., None] ** 1.2
            a = a * (1 - m) + b * m
        hl = np.clip((a.max(2) - .72) / .28, 0, 1)
        glow = np.asarray(Image.fromarray((hl * 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
                          .filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)).astype(np.float32)[..., None] / 255
        a = np.clip(a + glow * np.array([.16, .07, .02], np.float32), 0, 1)
        if s.get("word"):  # punch frames pop exposure on the cut
            a = a * (1 + .3 * (1 - ease(lt / .22)))
        return self.grade(a, s, p) * self.VIG * self.SCRIM

    @staticmethod
    def place(fr, L, cx, cy, al, sc=1.0, anchor="c"):
        if al <= .002: return
        if sc != 1.0:
            h0, w0 = L.shape[:2]
            L = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).resize((int(w0 * sc), int(h0 * sc)), Image.BICUBIC)).astype(np.float32) / 255
        lh, lw = L.shape[:2]
        x = int(cx * W - lw / 2) if anchor == "c" else (int(.065 * W) - 20 if anchor == "l" else int(.935 * W - lw + 20))
        y = int(cy * H - lh / 2)
        sub = L[max(0, -y):min(lh, H - y), max(0, -x):min(lw, W - x)]; y0, x0 = max(y, 0), max(x, 0)
        Aa = sub[..., 3:4] * min(al, 1)
        fr[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = fr[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] * (1 - Aa) + sub[..., :3] * Aa

    def frame(self, t, i):
        s = next((s for s in self.S if s["start"] <= t < s["start"] + s["dur"]), self.S[-1])
        lt = t - s["start"]; f = self.render(s, lt); last = s.get("final")
        if last: f = f * (1 - .62 * ease((lt - self.STAMP + .35) / .4))
        for kind, L, cx, cy, t0, t1, fin, fout in s["_texts"]:
            if not (t0 <= lt <= t1): continue
            fi = 1.0 if fin == 0 else ease((lt - t0) / fin); fo = 1.0 if fout == 0 else ease((t1 - lt) / fout)
            anchor = "l" if kind == "cl" else "r" if kind == "cr" else "c"
            self.place(f, L, cx, cy + (1 - fi) * .008, fi * fo, anchor=anchor)
        if last and lt >= self.STAMP:
            k = lt - self.STAMP
            self.place(f, self.SEAL, .5, .41, min(1, k / .06), 1 + .22 * (1 - ease(k / .16)) if k < .16 else 1.0)
            self.place(f, self.WORD, .5, .545, ease((k - .35) / .6))
            self.place(f, self.TAG2, .5, .60, ease((k - .75) / .6))
            self.place(f, self.TAG1, .5, .64, ease((k - 1.0) / .6))
        if not last and s is not self.S[0]:
            self.place(f, self.MINI, .085, .095, .92)
        lc = self.S[-1]["start"]; st = lc + self.STAMP
        if lc <= t < lc + .12: f = f + (1 - (t - lc) / .12) * .55
        if st <= t < st + .08: f = f + (1 - (t - st) / .08) * .25
        f = f * (1 + .012 * np.sin(t * 37.0) + .008 * np.sin(t * 13.3))
        f = f * ease(t / .5) * ease((self.TOTAL - t) / .8) + self.GR[i % 6] * .028
        return np.clip(f, 0, 1)

    # ---- sound ----
    def audio(self, path):
        sr = 48000; T = self.TOTAL; B = self.B; n = int(T * sr) + 1; tt = np.arange(n) / sr
        rng = np.random.default_rng(5); sig = np.zeros(n)
        def add(t0, x, g=1.0):
            i0 = int(t0 * sr)
            if 0 <= i0 < n: L = min(len(x), n - i0); sig[i0:i0 + L] += x[:L] * g
        def kick(g=1.0, f1=150, f0=42, dec=7.0, L=.55):
            tl = np.arange(int(L * sr)) / sr
            return (np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * np.exp(-tl * 30)) / sr) * np.exp(-tl * dec) + rng.normal(0, 1, len(tl)) * np.exp(-tl * 250) * .3) * g
        def hat():
            x = np.diff(rng.normal(0, 1, int(.06 * sr)), prepend=0); return x * np.exp(-np.arange(len(x)) / sr * 60) * .18
        lp = lambda x, k: np.convolve(x, np.ones(k) / k, mode="same")
        lc = self.S[-1]["start"]; stamp = lc + self.STAMP
        b1 = self.S[-2]["start"] if len(self.S) > 2 else lc - 2 * B
        bed = sum(a * np.sin(2 * np.pi * f * tt + ph) for f, a, ph in [(36.71, .35, 0), (73.42, .3, 1), (110, .14, 2), (146.83, .08, .5), (174.6, .05, 1.2)])
        bed *= (.35 + .65 * np.clip(tt / lc, 0, 1)) * (.8 + .2 * np.sin(2 * np.pi * tt / B / 2))
        bed[int(lc * sr):] *= .55; sig += bed * .5
        b0 = self.S[1]["start"] if len(self.S) > 2 else 0
        t = b0; hat_from = self.S[min(3, len(self.S) - 2)]["start"]
        while t < b1 - 1e-6:
            g = .45 + .55 * (t - b0) / max(b1 - b0, 1e-6); add(t, kick(g))
            if t >= hat_from: add(t + B / 2, hat(), .6 + .6 * (t - b0) / max(b1 - b0, 1e-6))
            t += B
        for s in self.S[:-1]:
            if s.get("word"): add(s["start"], kick(1.1, f1=180, dec=6, L=.6))
        t = b1
        while t < lc - .16:
            p = (t - b1) / (lc - b1); L = int(.09 * sr)
            add(t, lp(rng.normal(0, 1, L) * np.exp(-np.arange(L) / sr * 35), 3), .25 + .55 * p); add(t, kick(.5 + .4 * p, dec=10, L=.25))
            t += B / 2 * (1 - .75 * p)
        L = int(max(lc - b1 - .14, .3) * sr); tl = np.arange(L) / sr
        riser = rng.normal(0, 1, L); riser = (riser - lp(riser, 40)) * (tl / tl[-1]) ** 2.2 * .55
        tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (tl / tl[-1] * 2)) / sr) * (tl / tl[-1]) ** 2 * .25
        add(lc - .14 - L / sr, riser + tone)
        sig[int((lc - .14) * sr):int(lc * sr)] = 0
        L = int(4.5 * sr); tl = np.arange(L) / sr
        sub = np.sin(2 * np.pi * np.cumsum(28 + 62 * np.exp(-tl * 3)) / sr) * np.exp(-tl * .9) * 1.3
        braam = lp(sum(np.sign(np.sin(2 * np.pi * f * tl)) * a for f, a in [(55, .25), (82.4, .18), (110, .12)]), 60) * np.exp(-tl * 1.1) * 1.2
        add(lc, sub + braam + lp(rng.normal(0, 1, L), 6) * np.exp(-tl * 6) * .7 + kick(1.4, dec=4, L=4.5))
        L = int(3.0 * sr); tl = np.arange(L) / sr
        ring = sum(np.sin(2 * np.pi * f * tl) * a for f, a in [(523.3, .16), (1187, .08), (1873, .05), (261.6, .14)]) * np.exp(-tl * 2.2)
        add(stamp, kick(1.2, f1=220, f0=50, dec=9, L=3.0) + ring + lp(rng.normal(0, 1, L), 2) * np.exp(-tl * 40) * .6)
        pad = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(146.83, .07), (220, .06), (293.66, .05), (349.2, .035)])
        sig += pad * np.clip((tt - stamp) / 1.2, 0, 1) * np.clip((T - tt) / 1.5, 0, 1)
        sig *= np.clip(tt / .4, 0, 1)
        irL = int(2.4 * sr); ir = rng.normal(0, 1, irL) * np.exp(-np.arange(irL) / sr * 2.4); ir /= np.sqrt((ir ** 2).sum())
        N = 1 << int(np.ceil(np.log2(n + irL)))
        wet = np.fft.irfft(np.fft.rfft(sig, N) * np.fft.rfft(ir, N), N)[:n]
        mix = sig * .85 + wet * .32; mix = np.tanh(mix / np.abs(mix).max() * 2.6); mix = mix / np.abs(mix).max() * .93
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.stack([mix, np.roll(mix, 280)], 1) * 32767).astype(np.int16).tobytes())

    def write(self, out):
        wav = out + ".wav"; self.audio(wav); nf = int(self.TOTAL * FPS)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-i", wav, "-c:v", "libx264", "-preset", "slow", "-b:v", "10M", "-maxrate", "14M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
        for i in range(nf):
            ff.stdin.write((self.frame(i / FPS, i) * 255).astype(np.uint8).tobytes())
            if i % 96 == 0: print(f"{i}/{nf}", flush=True)
        ff.stdin.close(); ff.wait(); os.remove(wav)

    def preview(self, prefix):
        outs = []
        for k, s in enumerate(self.S):
            ts = s["start"] + (self.STAMP + 1.5 if s.get("final") else s["dur"] * .55)
            p = f"{prefix}_{k:02d}.jpg"; Image.fromarray((self.frame(ts, 0) * 255).astype(np.uint8)).resize((360, 640)).save(p, quality=86); outs.append(p)
        ims = [Image.open(p) for p in outs]; cols = min(len(ims), 6); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (360 * cols, 640 * rows))
        for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * 360, (k // cols) * 640))
        sheet.save(prefix + "_sheet.jpg", quality=85)
        for p in outs: os.remove(p)
        return prefix + "_sheet.jpg"

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8")); film = Film(spec)
    print(f"{spec['id']}: {film.TOTAL:.1f}s, {len(film.S)} shots")
    if "--preview" in sys.argv:
        print("sheet:", film.preview(os.path.join(ROOT, "tools", "film", "_preview_" + spec["id"])))
    else:
        out = os.path.join(ROOT, spec["out"]); os.makedirs(os.path.dirname(out), exist_ok=True); film.write(out); print("wrote", out)
