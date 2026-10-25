# 여백의 지도 · MARGIN ATLAS

인스타 감성 20~30대를 위한 소규모(3~10명) 역사·예술 여행 브랜드 사이트. 인생준준과는 별도 브랜드.

## 페이지
- `index.html` 메인 — 히어로 슬라이드, 여행 10선, RUN THE MAP 미리보기, 철학, 주인장 소개, 영상, 저널, 커뮤니티, FAQ, 문의
- `run.html` RUN THE MAP — 해외 러닝·트레킹 대회
- `privacy.html` 여백의 지도 전용 개인정보처리방침

## 데이터
- `journal.json` 저널(칼럼) · `community.json` 게시판
- `photo-data.js` 사진·출처(Unsplash) 목록, 여행·저널별 사진 묶음
- 대회(`races.json`)·필름(`films.json`)은 인생준준 저장소 것을 같이 씀.
  이 폴더가 인생준준 저장소 안에 있으면 `../races.json`을, 따로 떨어져 있으면
  `raw.githubusercontent.com/probe2928-crypto/lifejunjun/main/`에서 자동으로 불러옴.
- `runfx.js`는 인생준준 저장소 `runfx.js` 복사본(필름 인트로). 원본을 고치면 여기도 같이 복사.

## 독립 저장소로 옮길 때
이 폴더 내용을 새 저장소 루트에 그대로 올리고 GitHub Pages(main / root)만 켜면 됨.
그다음 `index.html`·`run.html`의 `og:url` 주소만 새 주소로 바꾸기.
