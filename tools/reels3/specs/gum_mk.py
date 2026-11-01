# Komodo v6+: word-timed captions (edge-tts boundaries), frame-accurate cuts, slam numbers, zoom+hit only on countdown cuts
import json, subprocess, sys
sys.path.insert(0, "/home/claude/r3")
from wordtimes import lead_silence, caption_times, norm
P = json.load(open('/home/claude/r3/gum/phrases.json'))
pref, tag = sys.argv[1], sys.argv[2]; TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
WB = json.load(open(pref + "words.json"))
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def sil(path, d): subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(d),path],check=True)
parts=[]; T=[]; LEAD=[]; t=0.10
sil("/tmp/g_sil0.wav", 0.10); parts.append("/tmp/g_sil0.wav")
for i,p in enumerate(P):
    src=f"{pref}{i:02d}.mp3"; w=f"/tmp/g_p{i:02d}.wav"; tp=TEMPO*p.get("tempo",1)
    LEAD.append(lead_silence(src))
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",src,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(round(tp,3)),"-ar","48000","-ac","1",w],check=True)
    if p.get("squeeze"):
        w2=w.replace(".wav","_q.wav")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",w,"-af",f"silenceremove=stop_periods=-1:stop_duration={p['squeeze']}:stop_threshold=-40dB","-ar","48000","-ac","1",w2],check=True); w=w2
    d=dur(w); parts.append(w); T.append((t,t+d)); t+=d
    if p["gap"]>0:
        s=f"/tmp/g_s{i:02d}.wav"; sil(s,p["gap"]); parts.append(s); t+=p["gap"]
open("/tmp/g_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/gum/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/g_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.25,3); st=lambda i: T[i][0]
def wt(i, word):  # absolute time a word starts being spoken in phrase i
    tp=TEMPO*P[i].get("tempo",1)
    for x in WB[f"{i:02d}"]:
        if norm(word) in norm(x["w"]): return st(i)+max(0,x["s"]-LEAD[i])/tp
    raise SystemExit(f"word {word} not in phrase {i}")
C="/home/claude/own/clips/"
SH="unsharp=5:5:0.35"
SHOP=C+"own_sg_shop.mp4"
plan=[(0,      SHOP,{"ss":1.2,"cx":0.5,"vf":SH,"zoom":[1.0,1.05]}),
      (st(1),  "/home/claude/r3/gum/c_gum.mp4",{"trans":"zoom","hit":True}),
      (st(2),  C+"mx_singapore_19088.mp4",{"ss":1.0}),
      (st(3),  "/home/claude/r3/gum/c_mrt.mp4",{}),
      (st(4),  SHOP,{"ss":3.0,"cx":0.55,"vf":SH,"zoom":[1.05,1.12]}),
      (st(5),  C+"mx_singapore_20177.mp4",{"ss":0.8,"cx":0.5}),
      (st(6),  C+"mx_singapore_28635.mp4",{"ss":1.0,"cx":0.5}),
      (st(7),  C+"mx_singapore_20174.mp4",{"ss":0.5,"cx":0.45}),
      (st(8),  SHOP,{"ss":0.4,"cx":0.5,"vf":SH,"zoom":[1.0,1.05]})]
shots=[]
for k,(t0,clip,kw) in enumerate(plan):
    t1=plan[k+1][0] if k+1<len(plan) else end
    s={"clip":clip,"dur":round(t1-t0,3)}; s.update(kw); shots.append(s)
subs=[]
for i,p in enumerate(P):
    if not p["cap"]: continue
    t0=st(i); t1=st(i+1) if i+1<len(P) else end
    tp=TEMPO*p.get("tempo",1)
    sb={"t0":round(t0,3),"t1":round(t1,3),"text":p["cap"],"wt":caption_times(p["cap"],WB[f"{i:02d}"],st(i),LEAD[i],tp,t0)}
    MAN={2:[None,"파는","들여오는","금지예요"],6:[None,"치과용이나","금연","껌만","약국에서"]}
    if i in MAN: sb["wt"]=[round(t0,3) if w is None else round(wt(i,w),3) for w in MAN[i]]
    if i==8: sb.update(t1=end)
    subs.append(sb)
K=[0,0,0,170]
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"싱가포르 편의점에선\n[절대] 못 사는 것","size":104,"yc":0.22,"stroke":10,"room":900,"fade":False},
    {"type":"tag","t0":st(1),"t1":st(2),"text":"자료 사진","size":38,"x":60,"y":1150,"bg":K},
    {"type":"tag","t0":st(2),"t1":st(3),"text":"자료 영상","size":38,"x":60,"y":1150,"bg":K},
    {"type":"tag","t0":st(3),"t1":st(4),"text":"자료 사진 · 싱가포르 MRT","size":38,"x":60,"y":1150,"bg":K},
    {"type":"tag","t0":st(5),"t1":st(7),"text":"자료 영상","size":38,"x":60,"y":1150,"bg":K},
    {"type":"tag","t0":st(7),"t1":st(8),"text":"자료 영상","size":38,"x":60,"y":1150,"bg":K}]
spec={"id":f"gum_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,"loop_tail":0,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.3,"hit":"/home/claude/r3/hit.wav","hit_vol":0.3,"hit_lead":0.11,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":120.0,"music_vol":0.15,"music_fo":0,
          "duck":[[round(st(5)-0.4,2),round(st(5)+0.6,2),0.0,0.06]],"voice":voice,"voice_delay":0.0},
 "cover_t":0.4,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/gum/gum_{tag}.mp4","cover":f"/home/claude/r3/gum/gum_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/gum/gum_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
