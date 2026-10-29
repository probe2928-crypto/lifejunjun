# Cat v6+: real-speed footage (no slow-mo beyond 1.25x), word-timed captions, frame-accurate cuts, sound-led turn
import json, subprocess, sys
sys.path.insert(0, "/home/claude/r3")
from wordtimes import lead_silence, caption_times, norm
P = json.load(open('/home/claude/r3/cat/phrases3.json'))
pref, tag = sys.argv[1], sys.argv[2]; TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
WB = json.load(open(pref + "words.json"))
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def sil(path, d): subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(d),path],check=True)
parts=[]; T={}; LEAD={}; t=0.10
sil("/tmp/c_sil0.wav", 0.10); parts.append("/tmp/c_sil0.wav")
for i,p in enumerate(P):
    if p.get("skip"): continue
    src=f"{pref}{i:02d}.mp3"; w=f"/tmp/c_p{i:02d}.wav"; tp=TEMPO*p.get("tempo",1)
    LEAD[i]=lead_silence(src)
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",src,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(round(tp,3)),"-ar","48000","-ac","1",w],check=True)
    d=dur(w); parts.append(w); T[i]=(t,t+d); t+=d
    if p["gap"]>0:
        s=f"/tmp/c_s{i:02d}.wav"; sil(s,p["gap"]); parts.append(s); t+=p["gap"]
open("/tmp/c_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/cat/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/c_list.txt","-c:a","pcm_s16le",voice],check=True)
last=max(T); end=round(T[last][1]+0.6,3); st=lambda i: T[i][0]
nxt=lambda i: min([T[j][0] for j in T if j>i], default=end)
C="/home/claude/own/clips/"; F="/home/claude/r3/fetch/"; ROT="transpose=2"; SH="unsharp=5:5:0.5"
SL=lambda f: "setpts=%s*PTS" % f
plan=[(0,      C+"own_sg_cat.mp4", {"ss":0.0,"cx":0.5,"zoom":[1.15,1.22],"zy":0.7,"vf":SH}),                     # hook: eye contact
      (st(1),  F+"mx_cat2_33152.mp4", {"ss":1.0,"cx":0.42,"zoom":[1.0,1.1],"zy":0.4,"pre":"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir"}),                                   # cat walks
      (st(2),  C+"hdb_blocks.mp4", {}),                                                                          # HDB blocks
      (st(3),  C+"own_sg_hdb.mp4", {"ss":4.2,"pre":ROT+","+SL(1.2),"cx":0.62,"zoom":[1.0,1.08],"zy":0.5}),       # corridor + tags
      (st(4),  F+"mx_cat_1539.mp4", {"ss":2.2,"cx":0.68,"zoom":[1.0,1.08]}),                                     # night eyes
      (st(5),  F+"mx_cat2_26381.mp4", {"ss":3.5,"cx":0.45,"pre":"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir"}),                                                     # kitten outside
      (st(6),  F+"mx_cat2_31936.mp4", {"ss":2.0,"cx":0.55,"hit":True,"zoom":[1.0,1.1]}),                        # TURN: cat on fence
      (st(8),  F+"mx_cat2_1778.mp4",  {"ss":4.0,"cx":0.5,"pre":"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir","vf":"boxblur=6:1,eq=brightness=-0.16"}),               # info pills
      (st(9),  C+"hdb_blocks.mp4",   {"ss":2.0,"zoom":[1.0,1.08]}),                  # estate today
      (st(10), F+"mx_cat2_22732.mp4", {"ss":1.0,"cx":0.45,"pre":"minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir","vf":"eq=brightness=-0.08","trans":"zoom"}),          # counter
      (st(12), C+"own_sg_cat.mp4",    {"ss":0.0,"cx":0.5,"zoom":[1.15,1.3],"zy":0.7,"vf":SH,"freeze":1.6,"freeze_sat":1.0})]                   # CTA, loops to hook
shots=[]
for k,(t0,clip,kw) in enumerate(plan):
    t1=plan[k+1][0] if k+1<len(plan) else end
    s={"clip":clip,"dur":round(t1-t0,3)}; s.update(kw); shots.append(s)
subs=[]
for i,p in enumerate(P):
    if p.get("skip") or not p["cap"]: continue
    t0=st(i); t1=nxt(i)
    tp=TEMPO*p.get("tempo",1)
    s={"t0":round(t0,3),"t1":round(t1,3),"text":p["cap"],"wt":caption_times(p["cap"],WB[f"{i:02d}"],st(i),LEAD[i],tp,t0)}
    if i==10: s["y"]=0.30
    if i==12: s.update(y=0.44,t1=end)
    subs.append(s)
G=[40,170,90,240]; R=[230,45,45,240]; K=[0,0,0,170]
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"싱가포르 아파트,\n고양이 키우면 [불법]?","size":120,"yc":0.30,"stroke":10,"room":800},
    {"type":"tag","t0":st(3)+0.25,"t1":st(4),"text":"소형견 1마리  허용","size":64,"x":90,"y":1100,"bg":G},
    {"type":"tag","t0":st(3)+1.0,"t1":st(4),"text":"고양이  금지","size":64,"x":90,"y":1220,"bg":R},
    {"type":"tag","t0":st(8),"t1":st(9),"text":"한 집에 최대 2마리","size":64,"x":90,"y":1000,"bg":G},
    {"type":"tag","t0":st(8)+0.7,"t1":st(9),"text":"마이크로칩","size":64,"x":90,"y":1120,"bg":G},
    {"type":"tag","t0":st(8)+1.4,"t1":st(9),"text":"정식 등록","size":64,"x":90,"y":1240,"bg":G},
    {"type":"counter","t0":st(10),"t1":nxt(10),"to":111000,"suffix":"+","dur":1.2,"size":190,"yc":0.62},
    {"type":"tag","t0":st(10)+0.4,"t1":nxt(10),"text":"2026년 8월 31일 기준","size":60,"x":250,"y":1330,"bg":K},
    {"type":"endcard","t0":st(12),"t1":end+0.1,"lines":["싱가포르 HDB"],"sub":"고양이 허용 2년째","sub_pill":False,"sub_size":60,"size":110,"yc":0.21,"panel":True}]
spec={"id":f"cat_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.4,"hit":"/home/claude/r3/hit.wav","hit_vol":0.5,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":14.0,"music_vol":0.16,
          "duck":[[round(st(6)-0.35,2),round(st(6)+0.02,2),0.12,0.15]],"voice":voice,"voice_delay":0.0},
 "cover_t":0.6,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/cat/cat_{tag}.mp4","cover":f"/home/claude/r3/cat/cat_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/cat/cat_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
