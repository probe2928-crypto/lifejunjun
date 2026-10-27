import json, copy
C="/home/claude/own/clips/"
shots=[("own_dol2_p5",2.4,0),("own_dol2_s6",3.5,0),("own_dol2_s1",2.9,0),("own_dol2_p2",2.2,0),("own_dol2_p3",3.8,0),
       ("own_dol2_p4",2.8,0),("own_dol2_p5",3.6,0.2),("own_dol2_s3",3.4,0),("own_dol2_s6",3.0,2.8),("own_dol2_s2",6.0,0)]
SH=[{"clip":C+c+".mp4","dur":d,"ss":ss} for c,d,ss in shots]
cues=[(0.2,2.4,"튀르키예에선\n매년 [딱 하루]"),(2.4,5.6,"아침 [9시 5분]이 되면\n나라 전체가 멈춥니다"),(6.1,8.5,"그 이유가\n이 궁전에 있어요"),
      (9.0,11.0,"[1938년 11월 10일]"),(11.1,14.7,"튀르키예를 세운 [아타튀르크]가\n이 방에서 세상을 떠났어요"),(15.1,17.4,"그때 시각이\n아침 [9시 5분]"),
      (17.8,21.2,"그래서 이 방 시계는\n지금도 [9시 5분]"),(21.4,23.2,"그리고 매년\n그 시각이 되면"),(23.3,25.7,"[사이렌]이 울리고\n사람도 차도"),
      (25.8,27.4,"[1분 동안] 멈춥니다"),(30.9,33.4,"가시면 이 시계를\n꼭 찾아보세요")]
AU={"music":"/home/claude/r3/raspberry_lofi.m4a","music_ss":20.67,"music_vol":0.18,"voice":"/home/claude/r3/voice_dolma3.mp3","voice_delay":0.2}
base={"fontdir":"/home/claude/r3/fonts","workdir":"/home/claude/r3/work","shots":SH,"audio":AU,"cover_t":1.0}
# P1 letterbox
p1=copy.deepcopy(base); p1.update(id="P1_letterbox",layout="letterbox",box=[0,430,1080,1080],
  headline={"lines":["튀르키예가 매년","[9시 5분]에 멈추는 이유"],"size":84},
  brand={"text":"인생준준","size":100,"sub":"먼저 공부해 온 길동무와 떠나는 역사 여행"},
  style={"head_font":"Pretendard-Black.otf","sub_font":"Pretendard-Bold.otf","sub_size":46,"brand_font":"BlackHanSans-Regular.ttf","end_font":"Pretendard-Black.otf","stroke":5},
  subs=[{"t0":a,"t1":b,"text":t.replace("[","").replace("]","")} for a,b,t in cues],
  overlays=[{"type":"arrow","t0":0.2,"t1":2.4,"x":170,"y":930,"len":170},{"type":"arrow","t0":17.8,"t1":21.2,"x":170,"y":930,"len":170},
            {"type":"endcard","t0":27.7,"t1":30.8,"lines":["'돌마바흐체 궁전'"],"sub":"튀르키예 이스탄불","size":84,"yc":0.50}],
  out="/home/claude/r3/P1_letterbox.mp4",cover="/home/claude/r3/P1.jpg")
# P2 cinematic full, big captions
p2=copy.deepcopy(base); p2.update(id="P2_cinematic",layout="full",
  style={"sub_font":"BlackHanSans-Regular.ttf","sub_size":104,"sub_y":0.36,"stroke":8,"shadow":0.55,"vignette":0.40,"end_font":"BlackHanSans-Regular.ttf","small_font":"Pretendard-Bold.otf"},
  subs=[{"t0":a,"t1":b,"text":t} for a,b,t in cues],
  overlays=[{"type":"arrow","t0":0.2,"t1":2.4,"x":150,"y":1020,"len":190},{"type":"arrow","t0":17.8,"t1":21.2,"x":150,"y":1020,"len":190},
            {"type":"endcard","t0":27.7,"t1":30.8,"lines":["'돌마바흐체 궁전'"],"sub":"튀르키예 이스탄불","size":110,"yc":0.36}],
  out="/home/claude/r3/P2_cinematic.mp4",cover="/home/claude/r3/P2.jpg")
# P3 explainer: smaller bottom captions, tags & badges
small=[]
for a,b,t in cues:
    parts=t.split("\n")
    if len(parts)==2:
        m=a+(b-a)*len(parts[0].replace('[','').replace(']',''))/max(1,len(t.replace('[','').replace(']','').replace('\n','')))
        small += [(a,m,parts[0]),(m,b,parts[1])]
    else: small.append((a,b,t))
p3=copy.deepcopy(base); p3.update(id="P3_explainer",layout="full",
  style={"sub_font":"Pretendard-Black.otf","sub_size":78,"sub_y":0.74,"stroke":6,"shadow":0.5,"vignette":0.30,"tag_font":"Pretendard-Bold.otf","end_font":"Pretendard-Black.otf","small_font":"Pretendard-Bold.otf"},
  subs=[{"t0":a,"t1":b,"text":t} for a,b,t in small],
  overlays=[{"type":"badge","t0":0.2,"t1":5.6,"text":"매년 11월 10일 · 09:05","x":60,"y":200,"size":40},
            {"type":"tag","t0":0.4,"t1":2.4,"text":"9시 5분에 멈춘 시계","x":560,"y":700,"size":46},
            {"type":"arrow","t0":0.4,"t1":2.4,"x":170,"y":1000,"len":160},
            {"type":"tag","t0":6.1,"t1":8.6,"text":"돌마바흐체 궁전","x":60,"y":220,"size":50},
            {"type":"badge","t0":8.8,"t1":14.7,"text":"1938.11.10","x":60,"y":200,"size":44},
            {"type":"tag","t0":11.2,"t1":14.7,"text":"아타튀르크가 숨진 방","x":60,"y":300,"size":50},
            {"type":"tag","t0":17.9,"t1":21.2,"text":"지금도 9시 5분","x":560,"y":700,"size":50},
            {"type":"arrow","t0":17.9,"t1":21.2,"x":170,"y":1000,"len":160},
            {"type":"badge","t0":21.4,"t1":27.4,"text":"매년 11.10 · 09:05 · 1분","x":60,"y":200,"size":40},
            {"type":"endcard","t0":27.7,"t1":30.8,"lines":["돌마바흐체 궁전"],"sub":"튀르키예 이스탄불","size":100,"yc":0.40}],
  out="/home/claude/r3/P3_explainer.mp4",cover="/home/claude/r3/P3.jpg")
for p in (p1,p2,p3):
    p["sheet_t"]=[1.2,4.0,12.5,19.5,24.5,29.0]
    json.dump(p,open(p["id"]+".json","w"),ensure_ascii=False,indent=1)
print("ok")
