import json
from PIL import Image, ImageDraw, ImageFont
ms=[json.loads(l) for l in open('/home/claude/ice/meta.jsonl')]
ms.sort(key=lambda m:m['filename'])
font=ImageFont.load_default()
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
except Exception: pass
MW=1920; LH=24
outs=[]
for gi in range(0,len(ms),12):
    rows=[]
    for m in ms[gi:gi+12]:
        im=Image.open(m['sheet']).convert('RGB')
        if im.width>MW: im=im.resize((MW,round(im.height*MW/im.width)))
        rows.append((m,im))
    W=min(MW,max(im.width for _,im in rows)); H=sum(LH+im.height+6 for _,im in rows)
    c=Image.new('RGB',(W,H),(15,15,15)); d=ImageDraw.Draw(c); y=0
    for m,im in rows:
        d.text((4,y+3),f"{m['filename']}  |  {m['duration']:.1f}s  |  {m['orientation']}  |  audio={'yes' if m['has_audio'] else 'no'}",fill=(255,230,120),font=font)
        y+=LH; c.paste(im,(0,y)); y+=im.height+6
    p=f'/home/claude/ice/overview_{gi//12+1:02d}.jpg'; c.save(p,quality=82); outs.append((p,c.size))
print(outs)
print(len(ms), round(sum(m['duration'] for m in ms),2))
for m in ms: print(f"{m['filename']} | {m['duration']:.1f}s | {m['orientation']} | {'yes' if m['has_audio'] else 'no'}")
