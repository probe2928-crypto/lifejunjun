# horizontal photo on a blurred cover background, feathered band edges, slow push-in
import sys, subprocess, numpy as np
from PIL import Image, ImageFilter
src, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
bandw = float(sys.argv[4]) if len(sys.argv) > 4 else 1.25   # band width relative to frame width (crop sides)
cy = float(sys.argv[5]) if len(sys.argv) > 5 else .5
W, H, FPS = 1080, 1920, 30
im = Image.open(src).convert("RGB")
strip = float(sys.argv[6]) if len(sys.argv) > 6 else 0
bg = im.crop((0, 0, im.width, int(im.height * strip))) if strip else im.copy(); s = max(W / bg.width, H / bg.height) * 1.1
bg = bg.resize((int(bg.width * s), int(bg.height * s)), Image.LANCZOS)
bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
bg = bg.filter(ImageFilter.GaussianBlur(40)); br = float(sys.argv[7]) if len(sys.argv) > 7 else .55; bg = Image.eval(bg, lambda v: int(v * br))
n = int(dur * FPS)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for i in range(n):
    z = 1 + .10 * i / max(n - 1, 1)
    bw = int(W * bandw * z); bh = int(im.height * bw / im.width)
    band = im.resize((bw, bh), Image.LANCZOS)
    m = np.ones((bh, bw), np.float32); f = 80
    r = np.minimum(np.arange(bh), np.arange(bh)[::-1]) / f
    m *= np.clip(r, 0, 1)[:, None]
    mask = Image.fromarray((m * 255).astype(np.uint8))
    fr = bg.copy(); fr.paste(band, ((W - bw) // 2, int(H * cy - bh / 2)), mask)
    p.stdin.write(fr.tobytes())
p.stdin.close(); p.wait(); print("ok", out)
