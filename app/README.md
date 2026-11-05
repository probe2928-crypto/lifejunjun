# 인생준준 iOS 앱

Capacitor 8 앱. 화면은 `src/`(HTML·CSS·JS, 프레임워크 없음), 빌드·TestFlight 업로드는 `probe2928-crypto/chainbrief` → Actions → **스토어 앱** (`only: lifejunjun`).

- **번들 ID:** `kr.lifejunjun.app` · 표시 이름 **인생준준**
- **탭:** 탑승(여행 탑승권 → 상세 → 관심 신청) · 여행 카드(나라별 매너·벌금·꿀팁, 오프라인) · 내 여권(다녀온 나라 도장·가고 싶은 곳, 기기 안에만 저장) · 라운지(카카오·인스타·유튜브·사이트)
- **데이터:** `src/data/trips.json`, `src/data/cards.json`. 앱에 사본이 들어가고, 실행 중엔 `https://probe2928-crypto.github.io/lifejunjun/app/src/data/*.json`의 최신본(`updated`가 같거나 새로우면)으로 바꿔 씀 → **여행·카드 추가는 이 JSON만 고치면 앱 업데이트 없이 반영**
- **관심 신청:** 사이트와 같은 FormSubmit(운영자 메일)로 보냄, 유입 `ios-app`. 실패하면 카카오·인스타·메일 안내
- **금지 표기:** 여행 가격 숫자, 가이드·인솔·해설, 결제·예약 확정처럼 보이는 문구
- **스토어:** 문구·심사 메모는 chainbrief `store/asc/lifejunjun.json`, 스크린샷은 `store/ios-*.png`(1320×2868)
- **개인정보:** `privacy.html` · 지원 `support.html`
- **앱스토어 개인정보 신고(Privacy Nutrition Label):** 연락처 정보(이름·이메일 주소 또는 카카오톡 ID) — 앱 기능(연락), 사용자와 연결됨, 추적 안 함. 그 외 수집 없음
