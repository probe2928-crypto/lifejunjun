# Komodo v6+: word-timed captions (edge-tts boundaries), frame-accurate cuts, slam numbers, zoom+hit only on countdown cuts
import json, subprocess, sys
sys.path.insert(0, "/home/claude/r3")
from wordtimes import lead_silence, caption_times, norm
P = json.load(open('/home/claude/r3/komodo/phrases3.json'))
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
voice=f"/home/claude/r3/komodo/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/k_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.7,3); st=lambda i: T[i][0]
def wt(i, word):  # absolute time a word starts being spoken in phrase i
    tp=TEMPO*P[i].get("tempo",1)
    for x in WB[f"{i:02d}"]:
        if norm(word) in norm(x["w"]): return st(i)+max(0,x["s"]-LEAD[i])/tp
    raise SystemExit(f"word {word} not in phrase {i}")
C="/home/claude/own/clips/"
plan=[(0,"kom_k1h",{}),
      (st(1),"kom_p1b",{"trans":"zoom","hit":True}),
      (st(3),"kom_m1c",{"trans":"zoom","hit":True,"zoom":[1.0,1.12],"zy":0.55}),
      (st(5),"kom_k3",{"trans":"zoom","hit":True}),
      (wt(6,"코모도왕도마뱀"),"kom_k2",{}),
      (st(7),"kom_k4",{"zoom":[1.0,1.12],"zx":0.62,"zy":0.55}),
      (st(8),"kom_d1",{}),
      (st(9),"kom_d2",{}),
      (st(10),"kom_d3",{"zoom":[1.0,1.08]})]
shots=[]
for k,(t0,n,kw) in enumerate(plan):
    t1=plan[k+1][0] if k+1<len(plan) else end
    s={"clip":C+n+".mp4","dur":round(t1-t0,3),"vf":"unsharp=5:5:0.4"}; s.update(kw); shots.append(s)
subs=[]
for i,p in enumerate(P):
    if not p["cap"]: continue
    t0=st(i); t1=st(i+1) if i+1<len(P) else end
    tp=TEMPO*p.get("tempo",1)
    s={"t0":round(t0,3),"t1":round(t1,3),"text":p["cap"],"wt":caption_times(p["cap"],WB[f"{i:02d}"],st(i),LEAD[i],tp,t0)}
    if i==10: s.update(y=0.58,t1=end)
    subs.append(s)
Y=(255,214,64,250)
num=lambda a,b,s:{"type":"text","t0":a,"t1":b,"text":f"[{s}]","size":420,"yc":0.40,"stroke":14,"room":760,"slam":True}
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"코모도에서\n꼭 봐야 할 장면 [3]","size":118,"yc":0.72,"stroke":11,"room":900},
    num(st(1),st(2),3), num(st(3),st(4),2), num(st(5),st(6),1),
    {"type":"badge","t0":st(2),"t1":st(3),"text":"No.3","size":60,"x":60,"y":250,"bg":Y},
    {"type":"badge","t0":st(4),"t1":st(5),"text":"No.2","size":60,"x":60,"y":250,"bg":Y},
    {"type":"badge","t0":st(6),"t1":st(8),"text":"No.1","size":60,"x":60,"y":250,"bg":Y},
    {"type":"endcard","t0":st(10),"t1":end+0.1,"lines":["코모도 원정"],"sub":"인도네시아 · 코모도 국립공원","sub_pill":False,"sub_size":64,"size":130,"yc":0.25,"panel":True}]
spec={"id":f"komodo_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,"trans_dur":0.2,
 "audio":{"whoosh":"/home/claude/r3/whoosh.wav","whoosh_vol":0.6,"hit":"/home/claude/r3/hit.wav","hit_vol":0.45,
          "music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":14.0,"music_vol":0.18,"voice":voice,"voice_delay":0.0},
 "cover_t":0.6,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,"word_reveal":True,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":760,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/komodo/komodo_{tag}.mp4","cover":f"/home/claude/r3/komodo/komodo_{tag}.jpg"}
json.dump(spec,open(f"/home/claude/r3/komodo/komodo_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end,"cuts",[round(p[0],2) for p in plan])
for s in subs: print(s["text"].replace("\n"," / "), [round(x,2) for x in s["wt"]])
