"""프라하(2026-06 체코·베를린 폴더, 6/15~16 현지) 숏츠 2편. 사용: python3 example_prague.py a|b"""
import sys
sys.path.insert(0, "/home/claude/reel")
from reel import build
base = dict(W=1080, H=1920, src_dir="/mnt/user-data/uploads/TripDownloads/2026-06_Czech_Berlin",
            meta="/home/claude/cz/meta.jsonl", out_dir="/home/claude/reel/out")
# A: 연대 비교형(한국 기준) — 천문시계 1410=태종 10년, 카를교 1357=공민왕, 성 비투스 1344~1929
A = dict(base, vo="/home/claude/reel/vo/cz_a2", vo_span=True, name="Prague_shorts_A_years", bpm=118, seed=31, root=43, shots=[
    dict(vo_i=0, key="IMG_3728", ss=0.3, max=1.6, minspeed=0.4, beats=7, hook=["600년 넘은 시계가", "[아직도] 돌아갑니다"], zoom="out"),
    dict(vo_i=1, key="IMG_3728", ss=1.85, max=1.05, minspeed=0.3, beats=5, chip="프라하 천문시계", cap="1410년 = 조선 [태종 10년]", flash=True),
    dict(key="IMG_3728", ss=4.4, max=2.6, beats=5, chip="구시가 광장", cap="1410년 = 조선 [태종 10년]", flash=True),
    dict(vo_i=3, key="IMG_3720", ss=0.3, max=2.2, beats=5, chip="카를교 · 1357년", cap="고려 [공민왕] 때 착공", flash=True, cx=0.3),
    dict(key="IMG_3720", ss=2.5, max=1.6, beats=5, chip="카를교 · 1357년", cap="고려 [공민왕] 때 착공", flash=True, cx=0.55),
    dict(vo_i=4, key="IMG_3686", ss=0.3, beats=5, chip="성 비투스 대성당", cap="1344 → [1929] 완공", flash=True),
    dict(key="IMG_3690", ss=6.0, beats=5, chip="성 비투스 대성당", cap="1344 → [1929] 완공", flash=True),
    dict(vo_i=5, key="IMG_3689", ss=0.3, beats=5, cap="완성까지 [585년]", cx=0.5),
    dict(vo_i=6, key="IMG_3674", ss=2.0, beats=6, cta=["프라하 가는 친구한테", "[보내주세요]"], zoom="none", fade_out=True, cx=0.55),
])
# B: 리스트형 — 프라하 성 꼭 볼 4곳 (A와 다른 컷)
B = dict(base, vo="/home/claude/reel/vo/cz_b2", vo_span=True, name="Prague_shorts_B_castle4", bpm=120, seed=32, root=45, shots=[
    dict(vo_i=0, key="IMG_3706", ss=0.3, beats=6, hook=["프라하 성 가면", "[이 4곳]은 꼭 보세요"], zoom="out", cx=0.45),
    dict(vo_i=1, key="IMG_3702", ss=3.6, beats=7, count=1, chip="성 비투스 대성당", cap="뒤쪽에서 봐야 [진짜 크기]", flash=True, cx=0.6),
    dict(vo_i=2, key="IMG_3691", ss=2.4, beats=7, count=2, chip="구왕궁", cap="천장을 [꼭] 올려다보세요", flash=True, cx=0.25),
    dict(vo_i=3, key="IMG_3705", ss=0.4, beats=7, count=3, chip="성 이르지 바실리카", cap="[10세기]에 처음 세운 교회", flash=True, cx=0.5),
    dict(vo_i=4, key="IMG_3706", ss=4.6, beats=6, count=4, chip="황금소로", cap="알록달록 [작은 집들]", flash=True, cx=0.5),
    dict(vo_i=5, key="IMG_3708", ss=0.3, beats=6, cap="22번지 = [카프카] 작업실", cap_y=0.72, cx=0.5, stab=False),
    dict(vo_i=6, key="IMG_3675", ss=3.5, beats=6, cta=["저장해두고", "[프라하 가서] 꺼내보세요"], zoom="none", fade_out=True),
])
for k in sys.argv[1:]: build({"a": A, "b": B}[k])
