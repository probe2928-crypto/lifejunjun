# usage: python3 mk2.py <voice_prefix e.g. /path/cat_Hyunsu_> <tag>
import json, subprocess, sys, os
P = json.load(open('/home/claude/r3/cat/phrases.json'))
pref, tag = sys.argv[1], sys.argv[2]
TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
parts=[]; T=[]; t=0.12
sil0="/tmp/cat_sil0.wav"; subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t","0.12",sil0],check=True); parts.append(sil0)
for i,p in enumerate(P):
    f=f"{pref}{i:02d}.mp3"; w=f"/tmp/cat_p{i:02d}.wav"
    # trim edge-tts leading/trailing silence
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",f,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(TEMPO),"-ar","48000","-ac","1",w],check=True)
    d=dur(w); parts.append(w); T.append((round(t,2),round(t+d,2))); t+=d
    if p["gap"]>0:
        s=f"/tmp/cat_s{i:02d}.wav"; subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(p["gap"]),s],check=True); parts.append(s); t+=p["gap"]
open("/tmp/cat_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/cat/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/cat_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.4,2)
st=lambda i: T[i][0]
C="/home/claude/own/clips/"; ROT="transpose=2"; SH="unsharp=5:5:0.6"
cuts=[0, st(1), st(2), st(4), st(6), st(8), st(9), st(10), st(11), st(12), end]
SL=lambda f: "setpts=%s*PTS" % f
clips=[(C+"own_sg_cat.mp4",{"ss":0.2,"cx":0.55,"zoom":[1.0,1.06],"zy":0.55,"vf":SH}),                      # P0 hook eye contact
       (C+"own_sg_cat.mp4",{"ss":2.1,"cx":0.5,"vf":SH,"pre":SL(1.9)}),                                     # P1 cat walks (clean 2.0-3.7)
       (C+"own_sg_hdb.mp4",{"ss":4.2,"pre":ROT+","+SL(2.0),"cx":0.62,"zoom":[1.0,1.12],"zy":0.5}),       # P2-3 corridor + badges
       (C+"own_sg_cat.mp4",{"ss":9.0,"cx":0.55,"vf":SH,"pre":SL(1.8)}),                                    # P4-5 fur close
       (C+"own_sg_cat.mp4",{"ss":0.9,"cx":0.55,"vf":SH,"zoom":[1.1,1.16],"zy":0.6}),                      # P6-7 turn: eye contact
       (C+"own_sg_cat.mp4",{"ss":2.0,"cx":0.5,"pre":SL(3.0),"vf":"boxblur=12:2,eq=brightness=-0.22"}),    # P8 info pills
       (C+"own_sg_shop.mp4",{"ss":1.0,"cx":0.5,"vf":SH}),                                                  # P9 estate today
       (C+"own_sg_cat.mp4",{"ss":9.0,"cx":0.55,"pre":SL(3.0),"vf":"eq=brightness=-0.15:saturation=0.8,"+SH}),  # P10 counter
       (C+"own_sg_hdb.mp4",{"ss":5.4,"pre":ROT,"cx":0.62,"zoom":[1.0,1.06],"zy":0.45}),                    # P11 end title
       (C+"own_sg_cat.mp4",{"ss":0.0,"cx":0.55,"pre":SL(2.0),"vf":SH})]                                    # P12 CTA over eye contact (loops)
shots=[dict(clip=c,dur=round(cuts[i+1]-cuts[i],2),**kw) for i,(c,kw) in enumerate(clips)]
subs=[]
for i,p in enumerate(P):
    if not p["cap"]: continue
    t0=st(i); t1=st(i+1) if i+1<len(P) else end
    s={"t0":t0,"t1":round(t1,2),"text":p["cap"]}
    if i==10: s["y"]=0.30
    if i==12: s.update(y=0.40,t1=end)
    subs.append(s)
G=[40,170,90,240]; R=[230,45,45,240]; K=[0,0,0,170]
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"싱가포르 아파트,\n고양이 키우면 [불법]?","size":120,"yc":0.30,"stroke":10,"room":800},
    {"type":"tag","t0":st(3)+0.25,"t1":st(4),"text":"소형견 1마리  허용","size":64,"x":90,"y":1100,"bg":G},
    {"type":"tag","t0":st(3)+1.0,"t1":st(4),"text":"고양이  금지","size":64,"x":90,"y":1220,"bg":R},
    {"type":"flash","t0":st(6),"t1":st(6)+0.18},
    {"type":"tag","t0":st(8),"t1":st(9),"text":"한 집에 최대 2마리","size":64,"x":90,"y":1000,"bg":G},
    {"type":"tag","t0":st(8)+0.7,"t1":st(9),"text":"마이크로칩","size":64,"x":90,"y":1120,"bg":G},
    {"type":"tag","t0":st(8)+1.4,"t1":st(9),"text":"정식 등록","size":64,"x":90,"y":1240,"bg":G},
    {"type":"counter","t0":st(10),"t1":st(11),"to":111000,"suffix":"+","dur":1.8,"size":190,"yc":0.47},
    {"type":"tag","t0":st(10)+0.4,"t1":st(11),"text":"2026년 8월 31일 기준","size":60,"x":250,"y":1150,"bg":K},
    {"type":"endcard","t0":st(11),"t1":st(12),"lines":["싱가포르 HDB"],"sub":"고양이 허용 2년째","sub_pill":False,"sub_size":64,"size":128,"yc":0.25,"panel":False}]
spec={"id":f"cat_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,
 "audio":{"music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":20.67,"music_vol":0.16,"voice":voice,"voice_delay":0.0},
 "cover_t":0.8,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/cat/cat_{tag}.mp4","cover":f"/home/claude/r3/cat/cat_{tag}.jpg",
 "sheet_t":[0.05,1.0,round(st(1)+.5,2),round(st(2)+.5,2),round(st(3)+1.5,2),round(st(6)+.3,2),round(st(8)+.5,2),round(st(10)+2.2,2),round(st(11)+1,2),round(end-0.8,2)]}
json.dump(spec,open(f"/home/claude/r3/cat/cat_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(c,2) for c in cuts])
