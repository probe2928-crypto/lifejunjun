#!/usr/bin/env python3
"""인생준준 reel covers — a different art direction every day.

usage:
  python3 tools/film/cover.py tools/film/specs/viralNN-x.json            # style = today's rotation
  python3 tools/film/cover.py tools/film/specs/viralNN-x.json --style noir
  python3 tools/film/cover.py tools/film/specs/viralNN-x.json --all      # contact sheet of every style

Writes media/covers/<spec id>.jpg (1080x1920). Key content sits inside the centre 3:4 band
(y 240–1680) so the profile-grid crop still reads.

Looks (inspired by — never copying logos, monograms or names of — the houses / artists they study):
  atelier    couture beauty: blush paper, Didone hairline serif, photo in an arch window, airy centre
  milano     austere Milanese minimalism: white page, framed photo, tiny black grotesk, strict left grid
  maximal    Roman maximalism: forest green, gold & burgundy, tilted polaroid collage, italic display serif
  kruger     conceptual-art statement: B/W photo, red bars, white condensed type
  swiss      International Typographic Style: giant numeral, circle crop, grid, red/black
  colorfield colour-field painting: two soft blocks sampled from the photo, quiet serif
  noir       Parisian noir: black page, small B/W photo, thin wide-spaced type
  editorial  magazine cover: full-bleed photo, homepage serif + mono
  parakeet   bold colour block: saturated green slab, photo bleeding off, italic serif
"""
import datetime, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
W, H = 1080, 1920
STYLES = ["atelier", "milano", "maximal", "kruger", "swiss", "colorfield", "noir", "editorial", "parakeet"]
RED = (200, 38, 28)

def F(name, size, var=None):
    f = ImageFont.truetype(name if name.startswith("/") else os.path.join(FD, name), size, index=1 if name.endswith(".ttc") else 0)
    if var is not None:
        try: f.set_variation_by_axes(var)
        except Exception: pass
    return f
NOTO_SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
BODONI = lambda s, w=400: F("BodoniModa[opsz,wght].ttf", s, [w, 96])
BODONI_I = lambda s, w=400: F("BodoniModa-Italic[opsz,wght].ttf", s, [w, 96])
PLAYFAIR_I = lambda s, w=900: F("PlayfairDisplay-Italic[wght].ttf", s, [w])
CORMORANT_I = lambda s, w=400: F("CormorantGaramond-Italic[wght].ttf", s, [w])
INSTR = lambda s: F("InstrumentSerif-Regular.ttf", s)
INSTR_I = lambda s: F("InstrumentSerif-Italic.ttf", s)
ANTON = lambda s: F("Anton-Regular.ttf", s)
ARCHIVO = lambda s: F("ArchivoBlack-Regular.ttf", s)
GROTESK = lambda s, w=500: F("SpaceGrotesk[wght].ttf", s, [w])
MONO = lambda s: F("IBMPlexMono-Medium.ttf", s)
KO_SERIF = lambda s: F("NanumMyeongjo-ExtraBold.ttf", s)
KO_SERIF_R = lambda s: F("NanumMyeongjo-Regular.ttf", s)
KO_BATANG = lambda s: F("GowunBatang-Regular.ttf", s)
KO_BATANG_B = lambda s: F("GowunBatang-Bold.ttf", s)
KO_HEAVY = lambda s: F("BlackHanSans-Regular.ttf", s)
KO_GOTHIC_B = lambda s: F("GothicA1-Black.ttf", s)
KO_GOTHIC_L = lambda s: F("GothicA1-Light.ttf", s)
KO_GOTHIC_T = lambda s: F("GothicA1-Thin.ttf", s)
KO_PLEX_L = lambda s: F("IBMPlexSansKR-Light.ttf", s)
KO_PLEX_M = lambda s: F("IBMPlexSansKR-Medium.ttf", s)
KO_NOTO = lambda s: F(NOTO_SERIF, s)

# ---------- drawing helpers ----------
def text(d, xy, s, font, fill, track=0.0, anchor="mm"):
    """draw with letter-spacing; anchor m=centre, l=left, r=right (horizontal) + vertical middle."""
    x, y = xy; sp = font.size * track
    ws = [font.getlength(c) for c in s]; tw = sum(ws) + sp * max(len(s) - 1, 0)
    x0 = x - tw / 2 if anchor[0] == "m" else (x if anchor[0] == "l" else x - tw)
    for c, w in zip(s, ws):
        d.text((x0, y), c, font=font, fill=fill, anchor="lm"); x0 += w + sp
    return tw

def fit_font(maker, s, maxw, start, track=0.0):
    size = start
    while size > 20:
        f = maker(size); w = sum(f.getlength(c) for c in s) + f.size * track * (len(s) - 1)
        if w <= maxw: return f
        size -= 4
    return maker(size)

def cover_crop(im, w, h, cx=.5, cy=.5, zoom=1.0):
    k = max(w / im.width, h / im.height) * zoom
    r = im.resize((max(w, int(im.width * k)), max(h, int(im.height * k))), Image.LANCZOS)
    x = int(min(max(cx * r.width - w / 2, 0), r.width - w)); y = int(min(max(cy * r.height - h / 2, 0), r.height - h))
    return r.crop((x, y, x + w, y + h))

def grain(im, amt=10, seed=1):
    a = np.asarray(im).astype(np.int16)
    n = np.random.default_rng(seed).normal(0, amt, (im.height, im.width, 1)).astype(np.int16)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))

def shadow_text(base, xy, s, font, fill=(255, 255, 255), track=0.0, blur=14, op=150, anchor="mm"):
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    text(d, xy, s, font, (0, 0, 0, op), track, anchor); lay = lay.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(lay); d2 = ImageDraw.Draw(base); text(d2, xy, s, font, fill, track, anchor)

def seal(px):
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, px - 1, px - 1), radius=int(px * .1), fill=RED + (255,))
    f = KO_NOTO(int(px * .36))
    for k, l in enumerate(["인생", "준준"]):
        d.text((px / 2, px * (.30 + k * .40)), l, font=f, fill="white", anchor="mm")
    return im

def palette(im, k=3):
    q = im.convert("RGB").resize((120, 120)).quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:k * 3]; cnt = sorted(q.getcolors(), reverse=True)
    return [tuple(pal[i * 3:i * 3 + 3]) for _, i in cnt]

# ---------- content from a viral spec ----------
class Content:
    def __init__(self, spec):
        h = spec["hook"]; c = spec.get("cover", {})
        self.id = spec["id"]; self.lines = h["title"].split("\n")
        self.title = " ".join(self.lines).replace("TOP 5", "").strip()
        self.kicker = h.get("kicker", "LIFEJUNJUN").replace("  ", " ")
        self.items = spec["items"]
        self.top = next((i for i in self.items if i["rank"] == 1), self.items[-1])
        self.places = [i["en"].split(",")[0].upper() for i in sorted(self.items, key=lambda i: -i["rank"])]
        t = self.title
        self.word = c.get("word") or ("Trek" if ("트레킹" in t or "걷" in t) else "Run" if ("RUN" in self.kicker or "달리" in t or "마라톤" in t) else "Ruins" if "유적" in t else "Voyage")
        self.statement = c.get("statement") or "아직 안 가봤다면"
        self.sub = h.get("sub", "").replace("TOP 5 · ", "")
        self.vol = c.get("vol") or spec["id"].split("-")[1]
        def load(p, kb=None):
            im = Image.open(os.path.join(ROOT, p)).convert("RGB")
            return im, (kb[2], kb[3]) if kb else (.5, .5)
        self.hero, self.hero_c = load(c.get("img", h["img"]), h.get("kb"))
        self.photos = [load(i["img"], i.get("kb")) for i in sorted(self.items, key=lambda i: i["rank"])]  # rank 1 first

# ---------- looks ----------
def atelier(C):
    bg = (243, 233, 226); ink = (58, 40, 40); rose = (176, 120, 120)
    im = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(im)
    text(d, (W / 2, 300), "LIFEJUNJUN  —  N° " + C.vol, GROTESK(24, 500), ink, .45)
    f = fit_font(lambda s: BODONI_I(s, 400), C.word, 900, 260)
    text(d, (W / 2, 470), C.word, f, ink, -.01)
    # arch window photo
    aw, ah, ax, ay = 620, 820, (W - 620) // 2, 640
    ph = cover_crop(C.hero, aw, ah, *C.hero_c, 1.05)
    ph = ImageEnhance.Color(ph).enhance(.85); ph = ImageEnhance.Brightness(ph).enhance(1.04)
    mask = Image.new("L", (aw, ah), 0); md = ImageDraw.Draw(mask)
    md.rectangle((0, aw // 2, aw, ah), fill=255); md.ellipse((0, 0, aw, aw), fill=255)
    im.paste(ph, (ax, ay), mask)
    d.arc((ax - 22, ay - 22, ax + aw + 22, ay + aw + 22), 180, 360, fill=rose, width=2)
    d.line((ax - 22, ay + aw // 2, ax - 22, ay + ah + 22), fill=rose, width=2); d.line((ax + aw + 22, ay + aw // 2, ax + aw + 22, ay + ah + 22), fill=rose, width=2)
    d.line((ax - 22, ay + ah + 22, ax + aw + 22, ay + ah + 22), fill=rose, width=2)
    text(d, (W / 2, 1560), C.title, fit_font(KO_BATANG_B, C.title, 900, 64), ink, .02)
    pl = "TOP  5   ·   " + "   ·   ".join(C.places[-3:])
    text(d, (W / 2, 1640), pl, fit_font(lambda z: GROTESK(z, 500), pl, 880, 22, .35), rose, .35)
    im.alpha_composite(seal(72), ((W - 72) // 2, 1730))
    return im

def milano(C):
    im = Image.new("RGBA", (W, H), (250, 250, 248, 255)); d = ImageDraw.Draw(im); ink = (12, 12, 12)
    L = 90
    text(d, (L, 290), "LIFEJUNJUN", GROTESK(30, 700), ink, .32, "lm")
    text(d, (W - L, 290), "N° " + C.vol + " / TOP 5", GROTESK(22, 500), ink, .3, "rm")
    d.line((L, 330, W - L, 330), fill=ink, width=2)
    ph = cover_crop(C.hero, W - 2 * L, 860, *C.hero_c, 1.08)
    ph = ImageEnhance.Color(ph).enhance(.7); ph = ImageEnhance.Contrast(ph).enhance(1.08)
    im.paste(ph, (L, 380))
    y = 1300
    for k, l in enumerate(C.lines):
        text(d, (L, y + k * 92), l, fit_font(KO_GOTHIC_B, l, W - 2 * L, 80), ink, -.02, "lm")
    d.rectangle((L, 1520, L + 300, 1566), fill=ink); text(d, (L + 20, 1543), C.sub[:16] or "TOP 5", KO_PLEX_M(26), (255, 255, 255), .02, "lm")
    for k, p in enumerate(C.places):
        text(d, (W - L, 1490 + k * 34), f"0{5 - k}  {p}", GROTESK(20, 400), ink, .2, "rm")
    text(d, (L, 1660), "RUN & TREK  ·  HISTORY  ·  TRAVEL TOGETHER", GROTESK(18, 400), (90, 90, 90), .3, "lm")
    return im

def maximal(C):
    g = (22, 52, 40); gold = (201, 162, 74); bur = (128, 26, 36); cream = (244, 234, 214)
    im = Image.new("RGBA", (W, H), g + (255,)); d = ImageDraw.Draw(im)
    for k in range(0, W, 12): d.line((k, 0, k, H), fill=(26, 58, 45), width=4)  # pinstripe
    d.rectangle((0, 250, W, 262), fill=gold); d.rectangle((0, 262, W, 286), fill=bur); d.rectangle((0, 286, W, 298), fill=gold)
    shots = [(C.photos[2], -8, 70, 560), (C.photos[1], 7, 560, 610), (C.photos[0], -2, 240, 840)]
    for (ph, c), ang, x, y in shots:
        p = cover_crop(ph, 420, 420, *c, 1.1); fr = Image.new("RGB", (460, 540), cream); fr.paste(p, (20, 20))
        fr = fr.convert("RGBA").rotate(ang, expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", fr.size, (0, 0, 0, 0)); sh.putalpha(fr.getchannel("A").point(lambda v: v * .5)); sh = sh.filter(ImageFilter.GaussianBlur(12))
        im.alpha_composite(sh, (x + 14, y + 18)); im.alpha_composite(fr, (x, y))
    text(d, (W / 2, 400), C.word + "!", PLAYFAIR_I(150), gold, -.01)
    text(d, (W / 2, 1480), C.title, fit_font(KO_SERIF, C.title, 940, 72), cream, .0)
    text(d, (W / 2, 1565), "· TOP FIVE ·  " + C.sub, fit_font(KO_SERIF_R, "· TOP FIVE ·  " + C.sub, 900, 34), gold, .04)
    d.rectangle((0, 1640, W, 1652), fill=gold); d.rectangle((0, 1652, W, 1676), fill=bur); d.rectangle((0, 1676, W, 1688), fill=gold)
    im.alpha_composite(seal(80), ((W - 80) // 2, 1730))
    return grain(im.convert("RGB"), 8, 3).convert("RGBA")

def kruger(C):
    ph = ImageOps.grayscale(cover_crop(C.hero, W, H, *C.hero_c, 1.1)); ph = ImageOps.autocontrast(ph, cutoff=2)
    ph = ImageEnhance.Contrast(ph).enhance(1.25)
    im = Image.merge("RGB", [ph] * 3).convert("RGBA"); d = ImageDraw.Draw(im); red = (224, 27, 34)
    lines = [C.statement, C.lines[0], C.lines[-1].replace(" TOP 5", "")]
    y = 520
    for k, l in enumerate(lines):
        f = fit_font(KO_HEAVY, l, 900, 104 if k else 84)
        tw = f.getlength(l); x = (W - tw) / 2
        d.rectangle((x - 26, y - f.size * .62, x + tw + 26, y + f.size * .62), fill=red)
        d.text((W / 2, y), l, font=f, fill="white", anchor="mm"); y += int(f.size * 1.5)
    f = ARCHIVO(46); l = "TOP 5. GO."; tw = f.getlength(l)
    d.rectangle(((W - tw) / 2 - 22, 1460 - 36, (W + tw) / 2 + 22, 1460 + 36), fill="white")
    d.text((W / 2, 1460), l, font=f, fill=red, anchor="mm")
    text(d, (W / 2, 1600), "LIFEJUNJUN  ·  " + C.places[-1], GROTESK(24, 600), (255, 255, 255), .35)
    return im

def swiss(C):
    bg = (238, 236, 230); ink = (17, 17, 17); im = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(im)
    for x in range(90, W, 150): d.line((x, 240, x, 1680), fill=(222, 220, 214), width=1)
    text(d, (90, 300), "TOP", ANTON(120), ink, .02, "lm")
    d.text((60, 820), "5", font=ANTON(900), fill=RED, anchor="lm")
    r = 230; cx, cy = 720, 760
    ph = cover_crop(C.hero, 2 * r, 2 * r, *C.hero_c, 1.15); m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r, 2 * r), fill=255)
    im.paste(ph, (cx - r, cy - r), m)
    for k, l in enumerate(C.lines):
        text(d, (90, 1420 + k * 86), l.replace(" TOP 5", ""), fit_font(KO_GOTHIC_B, l, 900, 76), ink, -.03, "lm")
    for k, p in enumerate(C.places):
        text(d, (W - 90, 1060 + k * 40), f"{5 - k:02d}  {p}", GROTESK(24, 600), ink, .1, "rm")
    d.line((90, 1580, W - 90, 1580), fill=ink, width=3)
    text(d, (90, 1630), C.kicker.replace(" · ", "  /  ").upper() + "  /  " + C.vol, GROTESK(22, 600), ink, .2, "lm")
    return im

def colorfield(C):
    cols = sorted(palette(C.hero, 6), key=lambda c: -(max(c) - min(c)) - sum(c) / 6)   # most chromatic & bright first
    cream = np.array([238, 230, 216])
    mix = lambda c, t: tuple(int(v) for v in np.array(c) * (1 - t) + cream * t)
    a, b = mix(cols[0], .25), mix(cols[1 if len(cols) > 1 else 0], .1)
    base = mix(cols[-1], .1)
    im = Image.new("RGB", (W, H), tuple(int(v * .6) for v in base)); d = ImageDraw.Draw(im)
    d.rectangle((110, 250, W - 110, 1010), fill=a); d.rectangle((110, 1070, W - 110, 1670), fill=b)
    im = im.filter(ImageFilter.GaussianBlur(22)); im = grain(im, 6, 5).convert("RGBA"); d = ImageDraw.Draw(im)
    ink = lambda c: (28, 24, 22) if (c[0] * .3 + c[1] * .59 + c[2] * .11) > 140 else (248, 242, 232)
    text(d, (W / 2, 630), C.word, INSTR_I(230), ink(a), -.01)
    text(d, (W / 2, 1290), C.title, fit_font(KO_BATANG_B, C.title, 820, 62), ink(b), .02)
    text(d, (W / 2, 1380), "TOP 5  ·  " + C.places[-1], GROTESK(22, 500), ink(b), .4)
    im.alpha_composite(seal(64), ((W - 64) // 2, 1500))
    return im

def noir(C):
    im = Image.new("RGBA", (W, H), (8, 8, 8, 255)); d = ImageDraw.Draw(im); wht = (236, 234, 230)
    text(d, (W / 2, 330), "L I F E J U N J U N", BODONI(34, 400), wht, .2)
    ph = ImageOps.grayscale(cover_crop(C.hero, 560, 700, *C.hero_c, 1.1)); ph = ImageEnhance.Contrast(ImageOps.autocontrast(ph, 1)).enhance(1.1)
    im.paste(Image.merge("RGB", [ph] * 3), ((W - 560) // 2, 520))
    text(d, (W / 2, 1360), C.title, fit_font(KO_GOTHIC_T, C.title, 900, 64), wht, .12)
    text(d, (W / 2, 1450), "TOP  FIVE", BODONI_I(48, 400), wht, .3)
    text(d, (W / 2, 1620), "   ".join(C.places[-3:]), GROTESK(18, 400), (150, 150, 150), .4)
    return im

def editorial(C):
    ph = cover_crop(C.hero, W, H, *C.hero_c, 1.12); ph = ImageEnhance.Color(ph).enhance(1.05)
    a = np.asarray(ph).astype(np.float32) / 255; yy = np.mgrid[0:H, 0:W][0] / H
    a = a * (1 - .55 * np.clip((.62 - yy) / .62, 0, 1) ** 1.1 - .55 * np.clip((yy - .72) / .28, 0, 1) ** 1.3)[..., None]
    im = Image.fromarray((a * 255).astype(np.uint8)).convert("RGBA")
    shadow_text(im, (W / 2, 320), C.kicker.upper(), MONO(26), (255, 255, 255), .32)
    d = ImageDraw.Draw(im); d.rectangle((W / 2 - 70, 356, W / 2 + 70, 360), fill=RED)
    for k, l in enumerate(C.lines):
        l2 = l.replace(" TOP 5", "")
        shadow_text(im, (W / 2, 450 + k * 150), l2, fit_font(KO_NOTO, l2, 960, 140), (255, 255, 255), -.02)
    shadow_text(im, (W / 2, 1010), "5", KO_NOTO(500), (255, 250, 240), -.02, 24, 170)
    d = ImageDraw.Draw(im); f = KO_PLEX_M(38); t = C.sub or "TOP 5"; tw = f.getlength(t)
    d.rectangle(((W - tw) / 2 - 26, 1330 - 32, (W + tw) / 2 + 26, 1330 + 32), fill=RED); d.text((W / 2, 1330), t, font=f, fill="white", anchor="mm")
    shadow_text(im, (W / 2, 1420), "  ·  ".join(C.places), MONO(22), (255, 255, 255), .22)
    im.alpha_composite(seal(100), ((W - 100) // 2, 1540))
    return im

def parakeet(C):
    green = (0, 150, 90); im = Image.new("RGBA", (W, H), green + (255,)); d = ImageDraw.Draw(im); wht = (250, 248, 240)
    ph = cover_crop(C.hero, 760, 1100, *C.hero_c, 1.05); im.paste(ph, (W - 760, 470))
    text(d, (80, 330), C.word.lower(), CORMORANT_I(220, 500), wht, -.02, "lm")
    for k, l in enumerate(C.lines):
        l2 = l.replace(" TOP 5", "")
        text(d, (80, 1640 + k * 0), "", KO_SERIF(10), wht)
    box = Image.new("RGBA", (620, 300), green + (255,)); bd = ImageDraw.Draw(box)
    for k, l in enumerate(C.lines):
        l2 = l.replace(" TOP 5", ""); bd.text((40, 70 + k * 92), l2, font=fit_font(KO_SERIF, l2, 560, 72), fill=wht, anchor="lm")
    im.alpha_composite(box, (40, 1300))
    text(d, (80, 1660), "TOP 5  —  LIFEJUNJUN", GROTESK(24, 600), wht, .35, "lm")
    im.alpha_composite(seal(70), (80, 1150))
    return im

LOOKS = dict(atelier=atelier, milano=milano, maximal=maximal, kruger=kruger, swiss=swiss, colorfield=colorfield, noir=noir, editorial=editorial, parakeet=parakeet)

def style_for(spec, date=None):
    """rotate looks by day; the two reels of the same day get neighbouring looks."""
    if spec.get("cover", {}).get("style") in LOOKS: return spec["cover"]["style"]
    d = date or datetime.date.today(); n = int(spec["id"].split("-")[1])
    return STYLES[(d.toordinal() * 2 + n) % len(STYLES)]

def make(spec, style):
    return LOOKS[style](Content(spec)).convert("RGB")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    if "--all" in sys.argv:
        ims = [make(spec, s).resize((360, 640)) for s in STYLES]
        sheet = Image.new("RGB", (360 * 5, 640 * 2), "white")
        for k, im in enumerate(ims): sheet.paste(im, ((k % 5) * 360, (k // 5) * 640))
        p = os.path.join(ROOT, "tools", "film", "_preview_covers_" + spec["id"] + ".jpg"); sheet.save(p, quality=85); print(p)
    else:
        st = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else style_for(spec)
        out = os.path.join(ROOT, "media", "covers", spec["id"] + ".jpg"); os.makedirs(os.path.dirname(out), exist_ok=True)
        make(spec, st).save(out, quality=92); print(st, out)
