# Komodo v6+: word-timed captions (edge-tts boundaries), frame-accurate cuts, slam numbers, zoom+hit only on countdown cuts
import json, subprocess, sys
sys.path.insert(0, "/home/claude/r3")
from wordtimes import lead_silence, caption_times, norm
P = json.load(open('/home/claude/r3/kw/phrases2.json'))
pref, tag = sys.argv[1], sys.argv[2]; TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
WB = json.load(open(pref + "words.json"))
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def sil(path, d): subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(d),path],check=True)
parts=[]; T=[]; LEAD=[]; t=0.10
sil("/tmp/k_sil0.wav", 0.10); parts.append("/tmp/k_sil0.wav")
for i,p in enumerate(P):
    src=f"{pref}{i:02d}.mp3"; w=f"/tmp/k_p{i:02d}.wav"; tp=TEMPO*p.get("tempo",1)
    LEAD.append(lead_silence(src))
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",src,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(round(tp,3)),"-ar","48000","-ac","1",w],check=True)
    if p.get("squeeze"):
        w2=w.replace(".wav","_q.wav")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",w,"-af",f"silenceremove=stop_periods=-1:stop_duration={p['squeeze']}:stop_threshold=-40dB","-ar","48000","-ac","1",w2],check=True); w=w2
    d=dur(w); parts.append(w); T.append((t,t+d)); t+=d
    if p["gap"]>0:
        s=f"/tmp/k_s{i:02d}.wav"; sil(s,p["gap"]); parts.append(s); t+=p["gap"]
open("/tmp/k_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/kw/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/k_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.25,3); st=lambda i: T[i][0]
def wt(i, word):  # absolute time a word starts being spoken in phrase i
    tp=TEMPO*P[i].get("tempo",1)
    for x in WB[f"{i:02d}"]:
        if norm(word) in norm(x["w"]): return st(i)+max(0,x["s"]-LEAD[i])/tp
    raise SystemExit(f"word {word} not in phrase {i}")
C="/home/claude/own/clips/"
plan=[(0,      "/home/claude/r3/kw/c_hook.mp4",{}),
      (st(1),  "/home/claude/r3/kw/c_trail.mp4",{"trans":"zoom","hit":True}),
      (st(2),  "/home/claude/r3/kw/c_body.mp4",{}),
      (st(3),  "/home/claude/r3/kw/c_stand.mp4",{"trans":"zoom"}),
      (st(4),  "/home/claude/r3/kw/c_foot.mp4",{"trans":"zoom","hit":True}),
      (st(5),  "/home/claude/r3/kw/c_mouth.mp4",{}),
      (st(6),  "/home/claude/r3/kw/c_head.mp4",{}),
      (st(7),  C+"kom_d1.mp4",{"zoom":[1.0,1.05]})]
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
    subs.append(sb)
K=[0,0,0,170]
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"코모도섬에선\n[절대] 혼자 걷지 마세요","size":104,"yc":0.22,"stroke":10,"room":900,"fade":False},
    {"type":"tag","t0":0.0,"t1":end,"text":"자료 사진","size":38,"x":60,"y":1150,"bg":K}]
spec={"id":f"kw_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,"loop_tail":0,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.3,"hit":"/home/claude/r3/hit.wav","hit_vol":0.3,"hit_lead":0.11,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":20.0,"music_vol":0.15,"music_fo":0,
          "duck":[],"voice":voice,"voice_delay":0.0},
 "cover_t":0.4,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/kw/kw_{tag}.mp4","cover":f"/home/claude/r3/kw/kw_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/kw/kw_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
