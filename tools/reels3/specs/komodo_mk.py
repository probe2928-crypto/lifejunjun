import json, subprocess, sys
P = json.load(open('/home/claude/r3/komodo/phrases.json'))
pref, tag = sys.argv[1], sys.argv[2]; TEMPO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
parts=[]; T=[]; t=0.12
s0="/tmp/k_sil0.wav"; subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t","0.12",s0],check=True); parts.append(s0)
for i,p in enumerate(P):
    w=f"/tmp/k_p{i:02d}.wav"
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",f"{pref}{i:02d}.mp3","-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo="+str(TEMPO),"-ar","48000","-ac","1",w],check=True)
    d=dur(w); parts.append(w); T.append((round(t,2),round(t+d,2))); t+=d
    if p["gap"]>0:
        s=f"/tmp/k_s{i:02d}.wav"; subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi","-i","anullsrc=r=48000:cl=mono","-t",str(p["gap"]),s],check=True); parts.append(s); t+=p["gap"]
open("/tmp/k_list.txt","w").writelines(f"file '{x}'\n" for x in parts)
voice=f"/home/claude/r3/komodo/voice_{tag}.wav"
subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","/tmp/k_list.txt","-c:a","pcm_s16le",voice],check=True)
end=round(T[-1][1]+0.8,2); st=lambda i: T[i][0]
C="/home/claude/own/clips/"
cuts=[0, st(1), st(2), st(3), st(5), st(6), st(7), st(8), st(9), st(10), end]
names=["kom_k1","kom_p1","kom_p2","kom_m1b","kom_k3","kom_k2","kom_k1","kom_d1","kom_d2","kom_d3"]
shots=[{"clip":C+n+".mp4","dur":round(cuts[i+1]-cuts[i],2),"vf":"unsharp=5:5:0.4"} for i,n in enumerate(names)]
subs=[]
for i,p in enumerate(P):
    if not p["cap"]: continue
    t0=st(i); t1=st(i+1) if i+1<len(P) else end
    s={"t0":t0,"t1":round(t1,2),"text":p["cap"]}
    if i==10: s.update(y=0.58,t1=end)
    subs.append(s)
Y=(255,214,64,250)
ov=[{"type":"text","t0":0.0,"t1":st(1),"text":"평생 한 번은 봐야 할\n코모도 장면 [3]","size":96,"yc":0.30,"stroke":10,"room":800},
    {"type":"text","t0":st(1),"t1":st(2),"text":"[3]","size":420,"yc":0.40,"stroke":14,"room":760},
    {"type":"text","t0":st(3),"t1":st(4),"text":"[2]","size":420,"yc":0.40,"stroke":14,"room":760},
    {"type":"text","t0":st(5),"t1":st(6),"text":"[1]","size":420,"yc":0.40,"stroke":14,"room":760},
    {"type":"flash","t0":st(1),"t1":st(1)+0.15},{"type":"flash","t0":st(3),"t1":st(3)+0.15},{"type":"flash","t0":st(5),"t1":st(5)+0.15},
    {"type":"badge","t0":st(2),"t1":st(3),"text":"No.3","size":60,"x":60,"y":300,"bg":Y},
    {"type":"badge","t0":st(4),"t1":st(5),"text":"No.2","size":60,"x":60,"y":300,"bg":Y},
    {"type":"badge","t0":st(6),"t1":st(8),"text":"No.1","size":60,"x":60,"y":300,"bg":Y},
    {"type":"tag","t0":0.0,"t1":end+0.1,"text":"자료 사진 · 위키미디어 커먼즈","size":40,"x":60,"y":228,"bg":[0,0,0,160]},
    {"type":"endcard","t0":st(10),"t1":end+0.1,"lines":["코모도 원정"],"sub":"인도네시아 · 코모도 국립공원","sub_pill":False,"sub_size":64,"size":130,"yc":0.25,"panel":True},
    {"type":"text","t0":T[10][0]+(T[10][1]-T[10][0])*0.55,"t1":end+0.1,"text":"일정 나오면 먼저 알려드려요\n(관심 등록)","size":64,"yc":0.74,"stroke":7,"room":760}]
spec={"id":f"komodo_{tag}","fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":shots,
 "audio":{"music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":20.67,"music_vol":0.18,"voice":voice,"voice_delay":0.0},
 "cover_t":0.8,"layout":"full",
 "style":{"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":9,"shadow":0.55,"vignette":0.2,
          "end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf","room":760,"tag_font":"Pretendard-Bold.otf"},
 "subs":subs,"overlays":ov,"out":f"/home/claude/r3/komodo/komodo_{tag}.mp4","cover":f"/home/claude/r3/komodo/komodo_{tag}.jpg",
 "sheet_t":[0.05,round(st(1)+.3,2),round(st(2)+.8,2),round(st(3)+.6,2),round(st(4)+.3,2),round(st(5)+.8,2),round(st(6)+.3,2),round(st(7)+.8,2),round(st(9)+.5,2),round(end-0.6,2)]}
json.dump(spec,open(f"/home/claude/r3/komodo/komodo_{tag}.json","w"),ensure_ascii=False,indent=1)
print("end",end)
