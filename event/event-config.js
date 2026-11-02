/* 인생준준 가입 혜택(역사 여행 노트 PDF) 설정 — 계획·근거: chainbrief ops/events/PLAN.md
   enabled:true = 공개. 로그인(site-auth) + ops/events/schema.sql + PDF 파일(pdf 경로)이 준비된 뒤에만 켠다.
   팀 규칙(ops/TEAM.md §3): 가격 숫자·가이드/인솔/해설 표현·긴급성 문구 금지. 할인 혜택은 여행업 등록 확인 후 세준이 정한다.
   미리보기: 로컬에서 ?event_preview=1 */
window.SITE_EVENT = {
  enabled: false,
  site: "lifejunjun",
  lang: "ko",
  kind: "welcome",
  id: "ljj-welcome",
  rulesUrl: document.currentScript ? document.currentScript.src.replace(/event-config\.js.*$/, "") : "event/",
  versions: { rules: "2026-11-02", consent: "ev-2026-11-02", marketing: "2026-11-02" },
  width: "1240px",
  theme: { ink: "#131313", paper: "#FFFFFF", accent: "#131313", muted: "#4A4B47", line: "#D5D6D1", wash: "#E9EAE5", radius: "4px",
           font: '"Noto Sans KR","Apple SD Gothic Neo",sans-serif', display: '"Noto Serif KR","Nanum Myeongjo",serif', dw: "700" },
  banner: {
    mount: "main#top > section.hero",
    where: "afterend",
    figure: "PDF",
    figureNote: "회원 선물",
    title: "가입하면 역사 여행 노트를 드려요",
    body: "떠나기 전에 읽어 두면 좋은 도시별 이야기와 연표, 걷는 길 메모를 한 권에 담았어요.",
    cta: "노트 받기",
    label: "가입 혜택"
  },
  welcome: {
    title: "역사 여행 노트 (PDF)",
    points: ["도시별 이야기와 한 장 연표", "함께 걸을 길과 동네 메모", "회원이면 누구나, 바로 내려받기"],
    note: "가입은 무료예요. 가입하면 이 페이지에서 바로 내려받을 수 있어요.",
    pdf: "",                                  // 예: "../media/note/history-travel-note.pdf" (파일 준비 후 입력)
    pdfLabel: "PDF 내려받기",
    done: function () { return "내 계정에 등록됐어요. 아래 버튼으로 내려받으세요."; }
  }
};
(function () {
  var C = window.SITE_EVENT, local = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  if (!C.enabled && !(local && /[?&]event_preview=1(&|$)/.test(location.search)) && !document.documentElement.hasAttribute("data-event-page")) return;
  var s = document.createElement("script"); s.src = (document.currentScript && document.currentScript.src || "").replace(/event-config\.js.*$/, "event.js"); s.defer = true; document.head.appendChild(s);
})();
