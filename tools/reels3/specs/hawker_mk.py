# Komodo v6+: word-timed captions (edge-tts boundaries), frame-accurate cuts, slam numbers, zoom+hit only on countdown cuts
import json, subprocess, sys
sys.path.insert(0, "/home/claude/r3")
from wordtimes import lead_silence, caption_times, norm
P = json.load(open('/home/claude/r3/hawker/phrases.json'))
pref, tag = sys.argv[1], sys.argv[2]; TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
WB = json.load(open(pref + "words.json"))
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def sil(path, d): subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(d),path],check=True)
parts=[]; T=[]; LEAD=[]; t=0.10
sil("/tmp/h_sil0.wav", 0.10); parts.append("/tmp/h_sil0.wav")
for i,p in enumerate(P):
    src=f"{pref}{i:02d}.mp3"; w=f"/tmp/h_p{i:02d}.wav"; tp=TEMPO*p.get("tempo",1)
    LEAD.append(lead_silence(src))
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",src,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(round(tp,3)),"-ar","48000","-ac","1",w],check=True)
    if p.get("squeeze"):
        w2=w.replace(".wav","_q.wav")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",w,"-af",f"silenceremove=stop_periods=-1:stop_duration={p['squeeze']}:stop_threshold=-40dB","-ar","48000","-ac","1",w2],check=True); w=w2
    d=dur(w); parts.append(w); T.append((t,t+d)); t+=d
    if p["gap"]>0:
        s=f"/tmp/h_s{i:02d}.wav"; sil(s,p["gap"]); parts.append(s); t+=p["gap"]
open("/tmp/h_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/hawker/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/h_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.25,3); st=lambda i: T[i][0]
def wt(i, word):  # absolute time a word starts being spoken in phrase i
    tp=TEMPO*P[i].get("tempo",1)
    for x in WB[f"{i:02d}"]:
        if norm(word) in norm(x["w"]): return st(i)+max(0,x["s"]-LEAD[i])/tp
    raise SystemExit(f"word {word} not in phrase {i}")
C="/home/claude/own/clips/"
SH="unsharp=5:5:0.5"
plan=[(0,                C+"hw3_hook.mp4",{}),
      (st(1),            C+"hw4_insert.mp4",{}),
      (st(2),            C+"hw3_chope.mp4",{}),
      (wt(2,"휴지"),      C+"hw4_push.mp4",{}),
      (st(3),            C+"own_sg_hawker.mp4",{"ss":5.0,"cx":0.62,"vf":SH}),
      (st(4),            C+"hw3_punggol.mp4",{"trans":"zoom","hit":True}),
      (wt(4,"싱가포르의"), C+"hw3_md_ex.mp4",{}),
      (st(5),            C+"hw3_taihwa.mp4",{}),
      (wt(5,"미쉐린"),    C+"hw3_hkchicken.mp4",{}),
      (st(6),            C+"hw3_tray1.mp4",{"trans":"zoom"}),
      (st(7),            C+"hw3_trayzone.mp4",{}),
      (st(8),            C+"hw3_tray2.mp4",{}),
      (wt(8,"처음엔"),    C+"hw4_crow.mp4",{}),
      (st(9),            C+"hw4_canberra.mp4",{}),
      (st(10),           C+"own_sg_hawker.mp4",{"ss":0.3,"cx":0.15,"vf":SH,"zoom":[1.05,1.12]}),
      (st(11),           C+"hw3_end.mp4",{})]
shots=[]
for k,(t0,clip,kw) in enumerate(plan):
    t1=plan[k+1][0] if k+1<len(plan) else end
    s={"clip":clip,"dur":round(t1-t0,3)}; s.update(kw); shots.append(s)
subs=[]
for i,p in enumerate(P):
    if not p["cap"]: continue
    t0=st(i); t1=st(i+1) if i+1<len(P) else end
    tp=TEMPO*p.get("tempo",1)
    s={"t0":round(t0,3),"t1":round(t1,3),"text":p["cap"],"wt":caption_times(p["cap"],WB[f"{i:02d}"],st(i),LEAD[i],tp,t0)}
    if i==9: s["y"]=0.33
    if i==4: s["y"]=0.58
    if i==11: s.update(y=0.47,t1=end)
    subs.append(s)
K=[0,0,0,170]; R=[230,45,45,240]
ov=[{"type":"chip","t0":0.0,"t1":st(1),"text":"[절대] 앉지 마세요","size":80,"yc":0.30},
    {"type":"tag","t0":0.0,"t1":st(1),"text":"※ 휴지는 이해를 돕기 위한 연출","size":40,"x":60,"y":300,"bg":K},
    {"type":"tag","t0":st(1),"t1":st(3),"text":"※ 연출","size":40,"x":60,"y":300,"bg":K},
    {"type":"tag","t0":st(11),"t1":end+0.1,"text":"※ 연출","size":40,"x":60,"y":1150,"bg":K},
    {"type":"counter","t0":round(wt(9,"구십삼")-0.45,2),"t1":st(10),"from":65,"to":93,"suffix":"%","suffix_always":True,"dur":1.2,"size":220,"yc":0.50},
    {"type":"text","t0":st(9),"t1":round(wt(9,"구십삼")-0.45,2),"text":"[65%]","size":220,"yc":0.50,"stroke":12,"room":900},
    {"type":"tag","t0":st(9)+0.4,"t1":st(10),"text":"2021.8 → 2024.4 · NEA","size":48,"x":300,"y":1110,"bg":K},
    {"type":"endcard","t0":st(11),"t1":end+0.1,"lines":["싱가포르 호커센터"],"size":112,"yc":0.245,"panel":True}]
spec={"id":f"hawker_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,"loop_tail":0,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.3,"hit":"/home/claude/r3/hit.wav","hit_vol":0.3,"hit_lead":0.11,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":14.0,"music_vol":0.15,"music_fo":0,
          "duck":[[round(st(6)-0.4,2),round(st(6)+0.65,2),0.0,0.06]],"voice":voice,"voice_delay":0.0},
 "cover_t":0.4,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/hawker/hawker_{tag}.mp4","cover":f"/home/claude/r3/hawker/hawker_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/hawker/hawker_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
