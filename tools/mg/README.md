# 모션그래픽 릴스 엔진 (mg)
레퍼런스: 세준이 11/2 보낸 키네틱 타이포 릴스(어두운 배경·네온 라임·글자 늘어남·빛줄기·노드 다이어그램).
- `mg.js`: 의존성 없는 트윈 엔진. `MG.T(대상, 시작초, 길이, {속성:[from,to]}, ease, stagger)`, `MG.split`(글자 단위), `MG.init()`, `MG.seek(t)`.
  속성 x y z scale scaleX scaleY rotate rotateX rotateY skewX opacity blur clipL/R/T/B ls bright. ease lin out out5 inOut in back expo.
  주의: 요소의 첫 트윈 from 값이 시작 전 상태가 된다(나중 트윈만 있는 속성은 `MG.set(대상,0,{...})`로 초기화).
- `render.js`: `node render.js scene.html out.mp4 15 30` (Playwright 프레임 단위 seek → JPEG 92 → ffmpeg). 점검: `node render.js scene.html chk/f 15 --frames 1,3.5,6`.
- `mkaudio.py`: 음악(덕킹)+whoosh/hit 박자+시계 틱+합성 사이렌 → m4a. 그다음 `ffmpeg -i v.mp4 -i a.m4a -map 0:v -map 1:a -c:v copy -c:a copy`.
- 폰트는 `../fonts/`(제작 컨테이너 /home/claude/r3/fonts) 기준. 글자는 y 270~1250 안, `white-space:nowrap`, 블랙한산스는 '·' '→' 글리프 없음.
- 샘플: `tr905.html` (튀르키예 11/10 09:05, 15초).
- **배경 영상 위에 얹기(11/2 추가):** `node render.js scene.html out.mp4 37.3 30 --bg bg.mp4` — 페이지를 투명 배경 PNG로 찍어 실제 영상 위에 합성. 어둡게 깔기·그리드·비네트는 HTML `.shade` 레이어에서. 음성판 예시: `specs/tr905n.html` + `specs/mkaudio_n.py`(목소리 시작 시각 배열·덕킹·실제 사이렌 소리).
- 첫 프레임(t=0)에 훅 문구가 다 떠 있어야 한다(`MG.set(...,0,{opacity:1})`). 검토 1차 6.6 → 첫 화면 완성·마무리 실용 정보(한국 시간)·출처 표기로 7.6.
