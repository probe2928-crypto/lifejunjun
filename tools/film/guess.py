#!/usr/bin/env python3
"""인생준준 '어디게?' guess-the-place reel — the 5M+ travel-reel grammar.

usage: python3 tools/film/guess.py tools/film/specs/guessNN-x.json [--preview]

What the very-high-view travel reels share (and this format copies):
  • show, don't promise — the most unreal shot is frame 1, no title card, no logo intro
  • one-line disbelief hook ("AI 아니고 실제 장소임") + a participation ask (guess in comments)
  • ~9 s and seamless loop (last frame == first frame) → rewatches push watch-time past 100 %
  • hints that make people think they know → comments; the answer is NOT in the video
    (it goes in the auto-comment), so viewers open the comments
  • 'tag who you'd go with' → sends
  • handheld micro-shake so stills read as footage, not a slideshow

spec: {"id","out","bpm":100,"n":1,
       "hook":"AI 아니고 실제 장소임", "ask":"어딘지 맞혀봐 — 댓글로",
       "shots":[{"img","kb":[s0,s1,cx,cy],"hint":"힌트 1 — …","beats":3}, …],   # first shot = hook shot
       "end":"정답은 댓글에 (스포 주의)", "tag":"같이 갈 사람 태그",
       "answer":"차른 캐니언, 카자흐스탄", "comment":"정답 공개 … (auto-comment text)",
       "caption":"…", "link":"…"}
"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viral import tline, pill, fit, place, seal, ease, eout, MONO, SANS_B, SANS_M, SERIF_K, ROOT  # noqa

W, H, FPS = 1080, 1920, 30

class Guess:
    def __init__(self, spec):
        self.spec = spec; self.B = 60 / spec.get("bpm", 100)
        shots = [dict(s) for s in spec["shots"]]
        end = dict(shots[0]); end["beats"] = spec.get("end_beats", 5); end["is_end"] = True
        end["kb"] = [shots[0]["kb"][1], shots[0]["kb"][0], shots[0]["kb"][2], shots[0]["kb"][3]]  # zoom back to frame-1 framing → loop
        self.S = shots + [end]; t = 0.
        for k, s in enumerate(self.S):
            s["dur"] = s.get("beats", 3) * self.B; s["start"] = t; t += s["dur"]
            im = Image.open(os.path.join(ROOT, s["img"])).convert("RGB")
            if max(im.size) < 2400:
                f = 2400 / max(im.size); im = im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS)
            im = ImageEnhance.Color(im).enhance(1.12); im = ImageEnhance.Contrast(im).enhance(1.05)
            s["_im"] = im.filter(ImageFilter.UnsharpMask(2, 70, 2))
            if s.get("hint"): s["_hint"] = pill(s["hint"], SANS_B, 40, bg=(20, 20, 20), track=.02)
        self.T = t
        n = spec.get("n", 1)
        self.KICK = tline(f"GUESS THE PLACE  ·  N° {n:02d}", MONO, 26, (255, 255, 255, 235), .32)
        self.HOOK = fit(tline(spec["hook"], SERIF_K, 96, track=-.01))
        self.ASK = pill(spec["ask"], SANS_B, 40, track=.02)
        self.END1 = fit(tline(spec["end"], SERIF_K, 80, track=-.01))
        self.END2 = tline(spec.get("tag", "같이 갈 사람 태그"), SANS_M, 42, (255, 255, 255, 240), .03)
        self.SEAL = seal(84)
        yy = np.mgrid[0:H, 0:W][0].astype(np.float32) / H
        self.SHADE = (1 - .58 * np.clip((.4 - yy) / .4, 0, 1) ** 1.2 - .35 * np.clip((yy - .74) / .26, 0, 1))[..., None]
        rng = np.random.default_rng(7); self.jx = rng.uniform(0, 6.28, 3); self.jy = rng.uniform(0, 6.28, 3)

    def shot(self, s, lt, t):
        im = s["_im"]; iw, ih = im.size; s0, s1, cx, cy = s["kb"]; p = lt / s["dur"]
        sc = s0 + (s1 - s0) * (eout(p) if not s.get("is_end") else ease(p))
        # handheld micro-shake (few px, layered sines) — reads as footage
        jx = sum(np.sin(t * f + ph) * a for f, ph, a in zip((1.3, 2.9, 7.1), self.jx, (5, 2.4, .8)))
        jy = sum(np.sin(t * f + ph) * a for f, ph, a in zip((1.1, 3.3, 6.7), self.jy, (4, 2.0, .7)))
        z = max(W / iw, H / ih) * max(sc, 1.02); vw, vh = W / z, H / z
        x0 = min(max(cx * iw - vw / 2 + jx / z, 0), iw - vw); y0 = min(max(cy * ih - vh / 2 + jy / z, 0), ih - vh)
        a = np.asarray(im.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), resample=Image.BILINEAR)).astype(np.float32) / 255
        return a * self.SHADE

    def frame(self, t):
        i = max(j for j, s in enumerate(self.S) if s["start"] <= t) if t < self.T else len(self.S) - 1
        s = self.S[i]; lt = t - s["start"]; f = self.shot(s, lt, t)
        up = lambda d, dur=.3: (ease((lt - d) / dur), (1 - eout((lt - d) / dur)) * .01)
        if i == 0:
            place(f, self.KICK, .5, .17, 1.0)
            place(f, self.HOOK, .5, .235, 1.0, 1 + .08 * (1 - eout(lt / .2)))   # on screen from frame 1
            a, r = up(.5); place(f, self.ASK, .5, .3 + r, a)
        elif s.get("is_end"):
            a, r = up(.1); place(f, self.END1, .5, .235 + r, a)
            a, r = up(.4); place(f, self.END2, .5, .29 + r, a)
            # fade the end text out over the last beat so the loop lands on a clean frame-1 picture
            if lt > s["dur"] - self.B * .8:
                k = (lt - (s["dur"] - self.B * .8)) / (self.B * .8)
                base = self.shot(s, lt, t); f[:] = f * (1 - ease(k)) + base * ease(k)
                place(f, self.KICK, .5, .17, ease(k)); place(f, self.HOOK, .5, .235, ease(k))
        else:
            place(f, self.KICK, .5, .17, .9)
            a, r = up(.08, .2); place(f, s["_hint"], .5, .24 + r, a, 1 + .1 * (1 - eout((lt - .08) / .18)))
        if not s.get("is_end") or lt < s["dur"] - self.B: place(f, self.SEAL, .085, .05, .9)
        if i > 0 and lt < .06: f = f + (1 - lt / .06) * .18
        return np.clip(f, 0, 1)

    def audio(self, path):
        sr = 48000; B = self.B; n = int(self.T * sr); tt = np.arange(n) / sr; rng = np.random.default_rng(11)
        lp = lambda x, k: np.convolve(x, np.ones(k) / k, mode="same")
        sig = np.zeros(n)
        def add(t0, x, g=1.):
            i0 = int(t0 * sr)
            if 0 <= i0 < n: L = min(len(x), n - i0); sig[i0:i0 + L] += x[:L] * g
        def kick(g=1., L=.35):
            tl = np.arange(int(L * sr)) / sr
            return np.sin(2 * np.pi * np.cumsum(46 + 90 * np.exp(-tl * 34)) / sr) * np.exp(-tl * 9) * g
        def tick():
            L = int(.04 * sr); x = np.diff(rng.normal(0, 1, L), prepend=0); return x * np.exp(-np.arange(L) / sr * 90) * .12
        # wind / air bed (periodic so the loop is seamless)
        air = lp(rng.normal(0, 1, n), 60) * 1.2
        air *= .6 + .4 * np.sin(2 * np.pi * tt / self.T)
        pad = sum(np.sin(2 * np.pi * f * tt) * a for f, a in [(110, .09), (164.8, .06), (220, .05), (277.2, .03), (329.6, .03)])
        sig += air * .35 + pad
        t = 0.; k = 0
        while t < self.T - 1e-6:
            add(t, kick(.9 if k % 2 == 0 else .55)); add(t + B / 2, tick()); add(t + B / 4, tick(), .5); add(t + 3 * B / 4, tick(), .5)
            t += B; k += 1
        for s in self.S[1:]:
            L = int(.25 * sr); x = rng.normal(0, 1, L); x = x - lp(x, 20)
            add(s["start"] - .2, x * np.sin(np.pi * np.arange(L) / L) ** 2 * .35)  # soft swish into each cut
        irL = int(1.4 * sr); ir = rng.normal(0, 1, irL) * np.exp(-np.arange(irL) / sr * 4); ir /= np.sqrt((ir ** 2).sum())
        N = 1 << int(np.ceil(np.log2(n + irL))); wet = np.fft.irfft(np.fft.rfft(sig, N) * np.fft.rfft(ir, N), N)
        wet = wet[:n] + np.concatenate([wet[n:n + irL], np.zeros(max(0, n - irL))])[:n]   # wrap the tail → seamless loop
        mix = sig + wet * .22; mix = np.tanh(mix / np.abs(mix).max() * 2.2); mix = mix / np.abs(mix).max() * .92
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.stack([mix, np.roll(mix, 200)], 1) * 32767).astype(np.int16).tobytes())

    def write(self, out):
        wav = out + ".wav"; self.audio(wav); nf = int(round(self.T * FPS))
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-i", wav, "-c:v", "libx264", "-preset", "slow", "-b:v", "11M", "-maxrate", "15M", "-bufsize", "22M", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
        for i in range(nf):
            ff.stdin.write((self.frame(i / FPS) * 255).astype(np.uint8).tobytes())
        ff.stdin.close(); ff.wait(); os.remove(wav)

    def preview(self, path):
        ts = [.3, .9] + [s["start"] + s["dur"] * .5 for s in self.S[1:]] + [self.T - .02]
        ims = [Image.fromarray((self.frame(t) * 255).astype(np.uint8)).resize((300, 533)) for t in ts]
        sheet = Image.new("RGB", (300 * len(ims), 533))
        for k, im in enumerate(ims): sheet.paste(im, (k * 300, 0))
        sheet.save(path, quality=85); return path

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8")); g = Guess(spec)
    print(f"{spec['id']}: {g.T:.1f}s")
    if "--preview" in sys.argv:
        print(g.preview(os.path.join(ROOT, "tools", "film", "_preview_" + spec["id"] + ".jpg")))
    else:
        out = os.path.join(ROOT, spec["out"]); g.write(out); print("wrote", out)
