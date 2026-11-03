/* 회원 로그인 설정 (인생준준) — 2026-11-02
   · 2026-11-03 키 입력 → 로그인 켜짐(이메일). url·anonKey 를 비우면 다시 아무것도 표시하지 않는다(화면 변화 0).
   · 켜는 법: Supabase → Project Settings → API 의 Project URL 과 anon(또는 publishable) 키를 아래 두 칸에 넣고 저장.
     서비스 롤(service_role / secret) 키는 절대 넣지 않는다.
   · 공용 로그인 모듈: https://probe2928-crypto.github.io/chainbrief/auth/auth.js (chainbrief 저장소 public/auth/auth.js)
   · 설명서: chainbrief 저장소 ops/auth/SETUP_GUIDE.md
   · 여행 모집 관심 신청자·가입자. 여행업 등록 전 — 결제·예약 확정 기능 없음. */
(function () {
  var c = window.SITE_AUTH = window.SITE_AUTH || {
    "url": "https://szsvihpghadpxhavdhqt.supabase.co",
    "anonKey": "sb_publishable_mRoGWPlaCUl-Z8vdR3NMDg_bXDinag1",
    "site": "lifejunjun",
    "lang": "ko",
    "providers": [
      "email"
    ],
    // 구글·카카오·애플: Supabase 공급자 설정이 끝나면 아래 목록에서 providers 로 옮기면 버튼이 켜진다 (2026-11-03 이메일만 우선 공개)
    "providersPending": [
      "kakao",
      "google",
      "apple"
    ],
    "naver": "hidden",
    "mimic": "header.top nav.main a",
    "brand": "인생준준",
    "links": {
      "terms": "terms.html",
      "privacy": "privacy.html"
    },
    "versions": {
      "terms": "2026-11-02",
      "privacy": "2026-11-02",
      "marketing": "2026-11-02"
    },
    "channels": [
      "email",
      "kakao",
      "sms"
    ],
    "night": true,
    "theme": {
      "ink": "#131313",
      "paper": "#FFFFFF",
      "accent": "#131313",
      "muted": "#4A4B47",
      "line": "#D5D6D1",
      "radius": "8px"
    },
    "iapNotice": false
  };
  if (!c.url || !c.anonKey) return;
  var s = document.createElement("script");
  s.src = "https://probe2928-crypto.github.io/chainbrief/auth/auth.js";
  s.defer = true;
  document.head.appendChild(s);
})();
