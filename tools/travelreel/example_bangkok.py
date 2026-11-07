import sys
sys.path.insert(0, "/home/claude/reel")
from reel import build
R = "20260523_015829"
base = dict(W=1080, H=1920, src_dir="/mnt/user-data/uploads/Videos/TripDownloads/2026-05_Bangkok",
            meta="/home/claude/bkk/meta.jsonl", out_dir="/home/claude/reel/out")

CUTS=[0,1.8,3.63,5.63,9.23,10.53,14.07,16.57,18.07,21.87,23.03,27.07,28.4,30.37,31.7,33.27,36.73,42.4,44.2,46.67,48.27,50.47,52.3,54.77,56.43,57.57,58.9,61.57,63.03,64.63,66.7,68.17,71.3]
S1 = dict(base, vo="/home/claude/reel/vo/bkk_s1b", name="Bangkok_shorts_1_food_v3", bpm=118, seed=21, root=45, shots=[
    dict(vo_i=0, key="IMG_2625", ss=0.3, beats=4, hook=["방콕 가면", "[이건 무조건] 먹어"], zoom="out"),
    dict(vo_i=1, key=R, ss=64.7, beats=4, count=1, chip="팟타이", cap="새우 듬뿍 [국민 메뉴]", flash=True),
    dict(vo_i=2, key=R, ss=63.1, beats=4, count=2, chip="카오만까이", cap="밤에 먹으면 [더 맛있음]"),
    dict(vo_i=3, key=R, ss=46.75, beats=3, count=3, chip="팟끄라파오", cap="계란 프라이 [필수]"),
    dict(vo_i=4, key=R, ss=30.45, beats=2, count=4, chip="로띠", cap="[달달한] 디저트"),
    dict(vo_i=5, key=R, ss=54.85, beats=3, count=5, chip="아보카도 코코넛 주스", cap="편의점 [꿀템]"),
    dict(vo_i=6, key="IMG_2658", ss=1.2, beats=6, cta=["저장해두고", "[방콕 가서] 꺼내보기"], zoom="none", fade_out=True),
])

S2 = dict(base, vo="/home/claude/reel/vo/bkk_s2b", name="Bangkok_shorts_2_business_v3", bpm=122, seed=22, root=43, shots=[
    dict(vo_i=0, key=R, ss=1.85, beats=4, hook=["비즈니스 행사로", "[방콕 출장] 왔습니다"], zoom="out"),
    dict(vo_i=1, key="IMG_2683", ss=0.8, beats=4, chip="Day 1 · 네트워킹 밋업", cap="업계 사람들 [다 모인 밤]", flash=True),
    dict(vo_i=2, key="IMG_2756", ss=1.6, beats=4, chip="Day 2 · AI·투자 컨퍼런스", flash=True),
    dict(key="IMG_2756", ss=3.6, beats=3),
    dict(vo_i=3, key="IMG_2758", ss=6.4, beats=6, cap="패널 세션 [자리 꽉]"),
    dict(vo_i=4, key=R, ss=42.5, beats=4, cap="새로 사귄 [친구들]", flash=True),
    dict(vo_i=5, key="IMG_2693", ss=0.6, beats=4, chip="애프터파티", vol=0.25),
    dict(vo_i=6, key="IMG_2789", ss=0.4, beats=4, cap="밤은 [루프탑]에서", flash=True),
    dict(vo_i=7, key=R, ss=66.8, beats=6, cta=["다음 비즈니스 행사", "[어디서 볼까요?]"], zoom="none", fade_out=True),
])

S3 = dict(base, vo="/home/claude/reel/vo/bkk_s3", name="Bangkok_shorts_3_night_v3", bpm=116, seed=23, root=40, shots=[
    dict(vo_i=0, key="IMG_2789", ss=0.3, beats=6, hook=["방콕의 밤은", "[보라색]입니다"], zoom="out"),
    dict(vo_i=1, key=R, ss=10.6, beats=6, chip="루프탑 레스토랑", flash=True),
    dict(vo_i=2, key="IMG_2785", ss=0.3, beats=5, cap="조명부터 [분위기 미침]"),
    dict(vo_i=3, key=R, ss=14.15, beats=4, chip="라탄 조명 레스토랑", flash=True),
    dict(vo_i=4, key="IMG_2693", ss=0.5, beats=4, chip="레드 라이트 바", vol=0.25, flash=True),
    dict(vo_i=5, key="IMG_2698", ss=14.4, beats=4, cx=0.62, cap="처음 만난 [친구들]과", vol=0.2),
    dict(vo_i=6, key=R, ss=18.15, beats=5, cap="새벽까지 [놀았다]"),
    dict(vo_i=7, key="IMG_2705", ss=0.5, beats=8, cx=0.15, cta=["방콕 밤 코스", "[저장] 해두세요"], zoom="none", fade_out=True, vol=0.2),
])

RUN = [k for k in sys.argv[1:] if k in ("s1","s2","s3")]

V = dict(base, vo="/home/claude/reel/vo/bkk_vb", W=1920, H=1080, name="Bangkok_vlog_03", bpm=112, seed=24, root=43, shots=[
    dict(vo_i=0, key=R, ss=0.2, beats=8, hook=["[BANGKOK]", "2026. 5 · 비즈니스 출장"], zoom="out"),
    dict(vo_i=1, key=R, ss=1.85, beats=4, chip="입장 팔찌 받고 시작", flash=True),
    dict(vo_i=2, key="IMG_2649", ss=0.3, beats=6, chip="호텔 · 수영장 뷰", cap="일단 [숙소부터]"),
    dict(vo_i=3, key=R, ss=64.7, beats=4, count=1, chip="팟타이", flash=True),
    dict(vo_i=4, key="IMG_2625", ss=0.6, beats=4, count=2, chip="카오만까이"),
    dict(vo_i=5, key=R, ss=46.75, beats=3, count=3, chip="팟끄라파오"),
    dict(key="IMG_2658", ss=1.0, beats=4, cap="더위엔 [얼음 가득]"),
    dict(vo_i=6, key="IMG_2676", ss=0.5, beats=8, chip="Day 1 · 네트워킹 밋업", cap="업계 사람들 [다 모인 밤]", flash=True),
    dict(key="IMG_2683", ss=0.8, beats=6),
    dict(vo_i=7, key=R, ss=27.15, beats=4, cap="밋업에서 [새 친구]"),
    dict(vo_i=8, key="IMG_2693", ss=0.5, beats=6, chip="애프터파티 · 레드 바", vol=0.3, flash=True),
    dict(key="IMG_2698", ss=14.4, beats=6, vol=0.3),
    dict(vo_i=9, key="IMG_2701", ss=34.4, beats=6, cap="처음 만난 [친구들]과", vol=0.3),
    dict(key="IMG_2705", ss=0.5, beats=6, vol=0.3),
    dict(vo_i=10, key="IMG_2756", ss=1.6, beats=6, chip="Day 2 · AI·투자 컨퍼런스", flash=True),
    dict(vo_i=11, key="IMG_2758", ss=6.4, beats=8, cap="패널 세션 [자리 꽉]"),
    dict(key=R, ss=42.5, beats=4, cap="행사장 [셀카 타임]"),
    dict(key=R, ss=56.5, beats=4),
    dict(vo_i=12, key="IMG_2789", ss=0.3, beats=8, chip="Day 2 · 밤", cap="밤은 [보라색 루프탑]", flash=True),
    dict(key=R, ss=10.6, beats=6),
    dict(key=R, ss=14.15, beats=4),
    dict(vo_i=13, key=R, ss=18.15, beats=6, cap="새벽까지 [놀았다]"),
    dict(vo_i=14, key=R, ss=66.8, beats=10, cta=["See you, [Bangkok]", "다음 출장은 어디로?"], zoom="none", fade_out=True),
])
for sh in V["shots"]:
    if sh["key"]==R and "max" not in sh:
        nxt=min(c for c in CUTS if c>sh["ss"]+0.05); sh["max"]=round(nxt-sh["ss"]-0.04,3)
        if sh["ss"]>=66.7: sh["max"]=round(71.2-sh["ss"],3)
if "vlog" in sys.argv: build(V)


for SP in (S1,S2,S3,V):
    for sh in SP["shots"]:
        if sh["key"]==R and "max" not in sh:
            nxt=min(c for c in CUTS if c>sh["ss"]+0.05); sh["max"]=round(nxt-sh["ss"]-0.04,3)
            if sh["ss"]>=66.7: sh["max"]=round(71.2-sh["ss"],3)
for k in RUN: build({"s1": S1, "s2": S2, "s3": S3}[k])
