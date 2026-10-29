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
end=round(T[-1][1]+0.7,3); st=lambda i: T[i][0]
def wt(i, word):  # absolute time a word starts being spoken in phrase i
    tp=TEMPO*P[i].get("tempo",1)
    for x in WB[f"{i:02d}"]:
        if norm(word) in norm(x["w"]): return st(i)+max(0,x["s"]-LEAD[i])/tp
    raise SystemExit(f"word {word} not in phrase {i}")
C="/home/claude/own/clips/"
SH="unsharp=5:5:0.5"
plan=[(0,          C+"hw_hook.mp4",{}),
      (st(1),      C+"hw_hook2.mp4",{}),
      (st(2),      C+"own_sg_hawker.mp4",{"ss":1.2,"cx":0.15,"vf":SH,"zoom":[1.05,1.12]}),
      (st(3),      C+"own_sg_hawker.mp4",{"ss":4.6,"cx":0.62,"vf":SH}),
      (st(4),      C+"hw_1973.mp4",{"trans":"zoom","hit":True}),
      (st(5),      C+"own_sg_trays.mp4",{"ss":2.4,"cx":0.5,"vf":SH}),
      (wt(5,"미쉐린"),C+"own_sg_trays.mp4",{"ss":10.6,"cx":0.45,"vf":SH,"zoom":[1.0,1.08]}),
      (st(6),      C+"hw_tray1.mp4",{"trans":"zoom","hit":True}),
      (st(8),      C+"hw_tray2.mp4",{}),
      (st(9),      C+"hw_punggol.mp4",{}),
      (st(10),     C+"hw_end.mp4",{}),
      (st(11),     C+"own_sg_hawker.mp4",{"ss":6.8,"cx":0.55,"vf":SH,"zoom":[1.0,1.06]})]
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
    if i==11: s.update(y=0.47,t1=end)
    subs.append(s)
K=[0,0,0,170]; R=[230,45,45,240]
ov=[{"type":"chip","t0":0.0,"t1":3.0,"text":"이 [휴지], 뭐지?","size":76,"yc":0.30},
    {"type":"tag","t0":0.0,"t1":st(2),"text":"※ 휴지는 이해를 돕기 위한 연출","size":34,"x":60,"y":290,"bg":K},
    {"type":"tag","t0":st(4)+0.2,"t1":st(5),"text":"1973년 싱가포르 호커센터","size":48,"x":60,"y":1080,"bg":K},
    {"type":"tag","t0":st(8)+0.3,"t1":st(9),"text":"2021년 9월 1일부터 단속","size":52,"x":60,"y":1080,"bg":R},
    {"type":"counter","t0":st(9),"t1":st(10),"to":93,"suffix":"%","dur":1.2,"size":220,"yc":0.50},
    {"type":"tag","t0":st(9)+0.4,"t1":st(10),"text":"2024년 4월 · NEA","size":48,"x":330,"y":1110,"bg":K},
    {"type":"endcard","t0":st(11),"t1":end+0.1,"lines":["싱가포르 호커센터"],"sub":"자리는 휴지로, 쟁반은 내가","sub_pill":False,"sub_size":58,"size":112,"yc":0.245,"panel":True}]
spec={"id":f"hawker_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,"loop_tail":0.4,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.5,"hit":"/home/claude/r3/hit.wav","hit_vol":0.45,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":14.0,"music_vol":0.15,
          "duck":[[round(st(6)-0.35,2),round(st(6)+0.02,2),0.15,0.15]],"voice":voice,"voice_delay":0.0},
 "cover_t":0.4,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":800,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/hawker/hawker_{tag}.mp4","cover":f"/home/claude/r3/hawker/hawker_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/hawker/hawker_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
