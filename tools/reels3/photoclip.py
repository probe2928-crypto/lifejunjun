# still photo -> moving vertical clip: cover crop around (cx,cy), zoom z0->z1, pan dx,dy (fraction of frame) with ease
import sys, json, subprocess
from PIL import Image
def make(src, out, dur, cx=.5, cy=.5, z0=1.0, z1=1.15, dx=0.0, dy=0.0, W=1080, H=1920, FPS=30):
    im = Image.open(src).convert("RGB")
    base = max(W / im.width, H / im.height)
    n = int(dur * FPS)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n):
        u = i / max(n - 1, 1); e = u * u * (3 - 2 * u) * .5 + u * .5
        z = z0 + (z1 - z0) * e; s = base * z
        cw, ch = W / s, H / s
        x = (cx + dx * (e - .5)) * im.width - cw / 2; y = (cy + dy * (e - .5)) * im.height - ch / 2
        x = min(max(x, 0), im.width - cw); y = min(max(y, 0), im.height - ch)
        fr = im.resize((W, H), Image.BICUBIC, box=(x, y, x + cw, y + ch))
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); print("ok", out)
if __name__ == "__main__":
    a = json.loads(sys.argv[1]); make(**a)
