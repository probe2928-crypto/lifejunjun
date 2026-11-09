"""베를린(6/18 현지)·프라하 저녁(6/15 현지) 숏츠 2편. 사용: python3 example_berlin.py a|b"""
import sys
sys.path.insert(0, "/home/claude/reel")
from reel import build
base = dict(W=1080, H=1920, src_dir="/mnt/user-data/uploads/TripDownloads/2026-06_Czech_Berlin",
            meta="/home/claude/cz/meta.jsonl", out_dir="/home/claude/reel/out")
# A: 리스트형 — 베를린 처음이면 이 5곳 (연도는 한국사 비교, 숫자 체크). v2: 메모리얼 훅, 돔 외관, CTA 파리저 광장
A = dict(base, vo="/home/claude/reel/vo/be_a3", vo_span=True, name="Berlin_shorts_A_5spots", bpm=120, seed=41, root=44, shots=[
    dict(vo_i=0, key="IMG_4027", ss=4.3, beats=4, hook=["베를린 처음이면", "[이 5곳]으로 끝"], zoom="out", cx=0.5),
    dict(vo_i=1, key="IMG_4005", ss=0.2, beats=4, count=1, chip="샤를로텐부르크 궁전", cap="1695년 착공 = 조선 [숙종] 때", flash=True, cx=0.5),
    dict(key="IMG_4006", ss=0.3, beats=3, count=1, chip="샤를로텐부르크 궁전", cap="1695년 착공 = 조선 [숙종] 때", cx=0.5),
    dict(vo_i=2, key="IMG_4024", ss=10.0, beats=4, count=2, chip="커리부어스트", cap="소시지 + [카레 케첩]", flash=True, cx=0.5),
    dict(key="IMG_4024", ss=14.2, beats=3, count=2, chip="커리부어스트", cap="소시지 + [카레 케첩]", cx=0.45),
    dict(vo_i=3, key="IMG_4064", ss=4.5, beats=5, count=3, chip="브란덴부르크 문", cap="1791년 완공 = [정조] 때", flash=True, cx=0.5),
    dict(vo_i=4, key="IMG_4076", ss=15.0, max=0.65, minspeed=0.35, beats=3, count=4, chip="국회의사당 유리 돔", cap="입장 [무료] · 예약 필수", flash=True, cx=0.45, cap_y=0.66),
    dict(key="IMG_4076", ss=15.72, max=0.55, minspeed=0.3, beats=4, count=4, chip="국회의사당 유리 돔", cap="입장 [무료] · 예약 필수", cx=0.5, cap_y=0.66),
    dict(vo_i=5, key="IMG_4079", ss=9.0, beats=4, count=5, chip="홀로코스트 메모리얼", cap="콘크리트 비석 [2,711개]", flash=True, cx=0.5),
    dict(key="IMG_4084", ss=4.3, beats=3, count=5, chip="홀로코스트 메모리얼", cap="콘크리트 비석 [2,711개]", cx=0.5),
    dict(vo_i=6, key="IMG_4065", ss=21.5, beats=4, cta=["저장해두고", "[베를린 가서] 꺼내보세요"], zoom="none", fade_out=True, cx=0.45),
])
# B: 리스트형 — 프라하 하루 마무리 3개 (성당 연주회·탱크 맥주·굴라시). v2: 연주 장면 훅, 맥주잔 컷, 실내 엔딩
B = dict(base, vo="/home/claude/reel/vo/cz_d", vo_span=True, name="Prague_shorts_C_evening3", bpm=112, seed=43, root=41, shots=[
    dict(vo_i=0, key="IMG_3778", ss=0.3, beats=3, hook=["프라하 하루 마무리", "[이 3개]면 완벽"], zoom="out", cx=0.5),
    dict(key="IMG_3780", ss=26.5, beats=3, hook=["프라하 하루 마무리", "[이 3개]면 완벽"], zoom="in", cx=0.5),
    dict(vo_i=1, key="IMG_3776", ss=0.3, beats=4, count=1, chip="클래식 연주회", cap="[바로크 성당]에서 듣는 연주", flash=True, cx=0.55),
    dict(key="IMG_3779", ss=0.3, beats=3, count=1, chip="클래식 연주회", cap="[바로크 성당]에서 듣는 연주", cx=0.5),
    dict(vo_i=2, key="IMG_3782", ss=0.4, max=1.6, minspeed=0.5, beats=4, count=2, chip="탱크 맥주", cap="[탱크]에서 바로 따라줘요", flash=True, cx=0.86),
    dict(key="IMG_3787", ss=0.3, max=1.6, minspeed=0.5, beats=3, count=2, chip="탱크 맥주", cap="[탱크]에서 바로 따라줘요", cx=0.05),
    dict(vo_i=3, key="IMG_3785", ss=0.1, max=2.3, minspeed=0.35, beats=5, count=3, chip="굴라시", cap="진한 [소고기 스튜]", flash=True, cx=0.5),
    dict(key="IMG_3787", ss=1.0, beats=3, count=3, chip="굴라시", cap="+ 맥주 [한 잔]", cx=0.2),
    dict(vo_i=4, key="IMG_3769", ss=1.0, beats=6, cta=["프라하 가는 친구한테", "[보내주세요]"], zoom="none", fade_out=True, cx=0.5),
])
for k in sys.argv[1:]: build({"a": A, "b": B}[k])
