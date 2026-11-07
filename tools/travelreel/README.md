# 여행 영상 엔진 (세준 직접 촬영 여행 영상 → 숏츠·브이로그)

세준 지시(2026-11-08): "세번째 영상 빼고 나머지 올리고 너가 알아서 앞으로 운영해 (퀄리티는 다음엔 조금 더 올려보자)".
피드백 누적: 흔들림 싫음(손떨림 보정 필수), AI 남자 성우 멘트 넣기, '코인' 단어 금지(비즈니스·투자·AI 행사로), 촌스러운 글씨·싼 티 금지, 잘 나가는 여행 릴스 수준.

## 원본
- PC `C:\Users\bluec\Videos\TripDownloads\<YYYY-MM_Place>\` (여행별 폴더, 아이폰 원본). 2025-11 아이슬란드, 2026-04 유럽(644개), 05 방콕(폴더 안 대부분은 한국 가족 영상 — 방콕은 5/19~20뿐, 아이 나오는 가족 영상 쓰지 말 것), 06 체코·베를린, 07 오키나와, 08 터키, 09 발리, 10 싱가포르·말레이시아.
- 가져오기: mcp__remote-devices__device_list_dir → device_stage_files(50개·500MB/회, 400MB 넘는 파일 불가) → /mnt/user-data/uploads/Videos/TripDownloads/<폴더>/
- proc.py / ov.py: 메타(meta.jsonl)·컨택트 시트·개요 이미지 → 장면 고르기(다른 여행·아이·사적인 장면 제외).

## 만들기
- 폰트: `npm pack pretendard` → package/dist/public/static/Pretendard-*.otf 를 /home/claude/fonts/package/... 에 (reel.py FD 경로).
- 성우: lifejunjun `fetch` 브랜치 fetch/jobs.json 에 {"type":"tts","name":..,"voice":"ko-KR-HyunsuMultilingualNeural","rate":"+10%","texts":[...]} push → 워크플로가 fetch/out/<name>_NN.mp3 생성(1분) → pull. 컨테이너에서 edge-tts 직접 호출은 막혀 있음.
- reel.py: 박자 컷·펀치 줌·화이트 플래시·vidstab 손떨림 보정·색보정·Pretendard 자막(노란 박스 강조)·위치 칩·번호 칩·CTA·성우(문장 길이에 맞춰 컷 길이 자동)·음악 자동 더킹. 원본이 짧으면 슬로모로 늘림(편집본 릴스 소스는 max로 컷 경계 지정).
- beat.py: 자체 제작 비트(저작권 걱정 없음).
- example_bangkok.py: 숏츠(먹방 리스트형·출장형·밤 분위기) + 가로 브이로그 예시.

## 올리기
- 웹용 재인코딩(crf 22, 50MB 이하) → main `media/ownNN-*.mp4` + 커버 jpg + media/queue.json 항목(skip:true, note에 tag) → push → Pages 배포 확인(gh run list).
- Metricool brand 7580610: IG·FB 릴스·Threads 한 게시물 + YouTube 쇼츠 따로. 첫 댓글 링크 https://probe2928-crypto.github.io/yeobaek/go/?r=<tag>. 캡션 끝에 '영상: 인생준준 직접 촬영 · 음악 자체 제작 · 내레이션 AI 음성'. 기존 예약과 시간 겹치지 않게(getScheduledPosts).
