import sys,subprocess,os
from PIL import Image,ImageDraw,ImageFont
p=sys.argv[1];out=sys.argv[2]
d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);tiles=[]
for t in range(int(d)+1):
    t=min(t+0.5,d-0.1);fp=f"/tmp/fs_{t}.jpg"
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",p,"-frames:v","1","-vf","scale=216:384",fp])
    im=Image.open(fp);ImageDraw.Draw(im).text((4,4),f"{t:.1f}",fill="red",font=f);tiles.append(im)
cols=10;rows=(len(tiles)+cols-1)//cols
c=Image.new("RGB",(cols*218,rows*386),(0,0,0))
for i,im in enumerate(tiles):c.paste(im,((i%cols)*218,(i//cols)*386))
c.save(out,quality=80);print(len(tiles))
