/* 인생준준 앱 — 탑승(여행)·여행 카드·내 여권·라운지. 프레임워크 없이, 네이티브 기능은 Capacitor 플러그인이 있을 때만 씀 */
(function () {
  "use strict";
  var REMOTE = "https://probe2928-crypto.github.io/lifejunjun/app/src/data/";
  var KAKAO = "https://open.kakao.com/o/gzvyLFTi";
  var INSTA = "https://www.instagram.com/lifejunjun/";
  var YT = "https://www.youtube.com/@kaniwast";
  var SITE = "https://probe2928-crypto.github.io/yeobaek/";
  var PRIVACY = "https://probe2928-crypto.github.io/lifejunjun/app/privacy.html";
  var MAIL = "probe2928@gmail.com";
  var VERSION = "1.0.0";

  var P = (window.Capacitor && window.Capacitor.Plugins) || {};

  var OS = (function () { try { return (window.Capacitor && window.Capacitor.getPlatform && window.Capacitor.getPlatform()) || "web"; } catch (e) { return "web"; } })();
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem("lj_" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem("lj_" + k, JSON.stringify(v)); } catch (e) {} }
  };
  function haptic(kind) { try { if (P.Haptics) { if (kind === "ok") P.Haptics.notification({ type: "SUCCESS" }); else P.Haptics.impact({ style: kind === "heavy" ? "HEAVY" : "MEDIUM" }); } } catch (e) {} }
  function openUrl(url) { try { if (P.Browser && /^https:/.test(url)) return P.Browser.open({ url: url, presentationStyle: "popover" }); } catch (e) {} window.open(url, "_blank"); }
  function toast(msg) { var t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(function () { t.hidden = true; }, 1800); }

  /* ── 데이터: 앱에 든 사본을 먼저 쓰고, 인터넷이 되면 사이트의 최신본으로 바꿈 ── */
  var DATA = { trips: [], cards: [] };
  function load(name) {
    var local = fetch("data/" + name + ".json").then(function (r) { return r.json(); });
    var remote = new Promise(function (res) {
      var ctl = window.AbortController ? new AbortController() : null;
      var to = setTimeout(function () { if (ctl) ctl.abort(); res(null); }, 4000);
      fetch(REMOTE + name + ".json?t=" + Date.now(), ctl ? { signal: ctl.signal } : {}).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { clearTimeout(to); res(j); }).catch(function () { clearTimeout(to); res(null); });
    });
    return local.then(function (l) {
      remote.then(function (r) { if (r && r[name] && r[name].length && r.updated >= l.updated) { DATA[name] = r[name]; render(); } });
      return l[name];
    });
  }

  /* ── 나라 목록 (내 여권) ── */
  var REGIONS = [
    ["동아시아", "#f15bb5", [["JP", "일본", "🇯🇵"], ["CN", "중국", "🇨🇳"], ["TW", "대만", "🇹🇼"], ["HK", "홍콩", "🇭🇰"], ["MO", "마카오", "🇲🇴"], ["MN", "몽골", "🇲🇳"]]],
    ["동남아시아", "#ff8a3d", [["VN", "베트남", "🇻🇳"], ["TH", "태국", "🇹🇭"], ["PH", "필리핀", "🇵🇭"], ["SG", "싱가포르", "🇸🇬"], ["MY", "말레이시아", "🇲🇾"], ["ID", "인도네시아", "🇮🇩"], ["KH", "캄보디아", "🇰🇭"], ["LA", "라오스", "🇱🇦"]]],
    ["남·중앙아시아·중동", "#e0902a", [["IN", "인도", "🇮🇳"], ["NP", "네팔", "🇳🇵"], ["UZ", "우즈베키스탄", "🇺🇿"], ["TR", "튀르키예", "🇹🇷"], ["AE", "아랍에미리트", "🇦🇪"], ["OM", "오만", "🇴🇲"], ["JO", "요르단", "🇯🇴"], ["EG", "이집트", "🇪🇬"], ["GE", "조지아", "🇬🇪"], ["AM", "아르메니아", "🇦🇲"]]],
    ["유럽", "#2f80ed", [["IT", "이탈리아", "🇮🇹"], ["FR", "프랑스", "🇫🇷"], ["ES", "스페인", "🇪🇸"], ["PT", "포르투갈", "🇵🇹"], ["GB", "영국", "🇬🇧"], ["DE", "독일", "🇩🇪"], ["CH", "스위스", "🇨🇭"], ["CZ", "체코", "🇨🇿"], ["AT", "오스트리아", "🇦🇹"], ["GR", "그리스", "🇬🇷"], ["HR", "크로아티아", "🇭🇷"], ["IS", "아이슬란드", "🇮🇸"], ["NO", "노르웨이", "🇳🇴"]]],
    ["아메리카·오세아니아", "#00b894", [["US", "미국", "🇺🇸"], ["CA", "캐나다", "🇨🇦"], ["MX", "멕시코", "🇲🇽"], ["PE", "페루", "🇵🇪"], ["AU", "호주", "🇦🇺"], ["NZ", "뉴질랜드", "🇳🇿"]]]
  ];
  var CTY = {}; REGIONS.forEach(function (r) { r[2].forEach(function (c) { CTY[c[0]] = { code: c[0], name: c[1], flag: c[2], region: r[0], color: r[1] }; }); });

  /* ── 라우팅: 탭 4개 + 여행 상세 시트 ── */
  var state = { tab: store.get("tab", "home"), cardFilter: "전체", mode: "visit", fresh: null };
  var TITLES = { home: "탑승", cards: "여행 카드", passport: "내 여권", lounge: "라운지" };
  function setTab(t) {
    state.tab = t; store.set("tab", t);
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (b) { b.classList.toggle("on", b.dataset.tab === t); b.setAttribute("aria-current", b.dataset.tab === t ? "page" : "false"); });
    $("#topTitle").textContent = TITLES[t];
    render(); window.scrollTo(0, 0);
  }
  function render(quiet) {
    var v = $("#view");
    if (state.tab === "home") v.innerHTML = viewHome();
    else if (state.tab === "cards") v.innerHTML = viewCards();
    else if (state.tab === "passport") v.innerHTML = viewPassport();
    else v.innerHTML = viewLounge();
    if (quiet) return;
    v.classList.remove("enter"); void v.offsetWidth; v.classList.add("enter");
    reveal(v);
  }

  function dday(start) {
    var s = new Date(start + "T00:00:00+09:00"), now = new Date(), d = Math.ceil((s - now) / 864e5);
    return d > 0 ? "D-" + d : d === 0 ? "D-DAY" : "다음 일정 준비 중";
  }

  /* ── 탑승 (홈) ── */
  function viewHome() {
    var t = DATA.trips || [];
    return '<section class="hero"><img class="scene" src="img/scene.svg" alt="">' +
      '<div class="txt"><div class="eyebrow">함께 가는 역사 여행</div>' +
      '<h1>혼자 가긴 무섭고,<br>단체 패키지는 싫다면</h1>' +
      '<p>먼저 공부해 온 길동무와 3~10명이 함께 걷는 작은 여행이에요. 유적은 깊게, 박물관은 천천히, 밥은 현지 사람들이 줄 서는 곳에서.</p>' +
      '<div class="row"><span class="chip">🧭 3명 모이면 출발</span><span class="chip">🙋 혼자 와도 돼요</span><span class="chip">✍️ 관심 신청은 결제 아니에요</span></div></div></section>' +
      '<div class="flyline" aria-hidden="true"><img src="img/fly.svg" alt=""></div>' +
      '<div class="sec-t">탑승 대기 중인 여행 <small>' + t.length + '편</small></div>' +
      '<div class="passes">' + t.map(function (x) {
        return '<button class="pass" data-trip="' + esc(x.id) + '" style="--g1:' + x.grad[0] + ';--g2:' + x.grad[1] + '" aria-label="' + esc(x.country + " 여행 자세히 보기") + '">' +
          '<div class="pass-img" style="background-image:url(' + esc(x.img) + ')"><span class="flag">' + x.flag + '</span><span class="dday">' + dday(x.start) + '</span></div>' +
          '<div class="route"><span>ICN</span><i></i><span>' + esc(x.code) + '</span></div>' +
          '<div class="pass-body"><div class="city">' + esc(x.country) + ' · ' + esc(x.city) + '</div>' +
          '<div><div class="k">출발 후보일</div><div class="v">' + esc(x.dates) + '</div></div>' +
          '<div style="text-align:right"><div class="k">기간</div><div class="v">' + esc(x.nights.split(" · ")[0]) + '</div></div>' +
          '<div class="lead">' + esc(x.lead) + '</div>' +
          '<div class="go"><span>자세히 보고 관심 신청 →</span><span class="barcode" aria-hidden="true"></span></div></div></button>';
      }).join("") + '</div>' +
      '<div class="sec-t">같이 가는 사람</div>' +
      '<div class="card about"><div class="face"><span>🧳</span></div><div><b>인생준준 세준</b><p>사학과를 나와 5년 동안 40번 넘게 해외를 다니며 역사 공부를 이어온 여행자예요. 유적 앞에서 같이 읽고, 같이 걷고, 같이 먹는 여행을 만들어요.</p></div></div>';
  }

  /* ── 여행 상세 + 관심 신청 ── */
  function openTrip(id) {
    var x = (DATA.trips || []).filter(function (t) { return t.id === id; })[0]; if (!x) return;
    var s = $("#sheet");
    s.style.setProperty("--g1", x.grad[0]); s.style.setProperty("--g2", x.grad[1]);
    s.innerHTML = '<button class="close" data-close aria-label="닫기">✕</button>' +
      '<div class="d-hero" style="background-image:url(' + esc(x.img) + ')"><img class="clouds c2" src="img/cloudband.svg" alt=""><img class="clouds" src="img/cloudband.svg" alt=""></div>' +
      '<div class="d-body"><div class="d-title"><div class="eyebrow">' + x.flag + ' ' + esc(x.country) + ' · ' + esc(x.city) + '</div><h2>' + esc(x.en) + '</h2><div><span class="chip">' + dday(x.start) + '</span></div></div>' +
      '<div class="meta"><div><div class="k">출발 후보일</div><div class="v">' + esc(x.dates) + '</div></div><div><div class="k">기간</div><div class="v">' + esc(x.nights) + '</div></div><div><div class="k">인원</div><div class="v">' + esc(x.group) + '</div></div></div>' +
      '<div class="d-lead">' + esc(x.lead) + '</div>' +
      '<div class="sec-t">왜 ' + esc(x.country) + '일까</div>' + x.why.map(function (p) { return '<p class="d-p">' + esc(p) + '</p>'; }).join("") +
      '<div class="sec-t">이 여행에서 만나는 것</div><div class="see">' + x.see.map(function (p, i) { return '<div data-n="0' + (i + 1) + '">' + esc(p) + '</div>'; }).join("") + '</div>' +
      '<div class="sec-t">하루 흐름 예시 <small>인원·날씨·항공편에 따라 함께 조정해요</small></div><ol class="flow">' + x.flow.map(function (f) { return '<li><span class="day">' + esc(f[0]) + '</span><span class="what">' + esc(f[1]) + '</span></li>'; }).join("") + '</ol>' +
      '<div class="sec-t">자주 묻는 질문</div><div class="faq">' +
      faq("혼자 신청해도 돼요?", "네, 대부분 혼자 신청해요. 3명이 모이면 출발하는 소규모 여행이라 처음 만나도 금방 편해져요.") +
      faq("신청하면 결제해야 하나요?", "아니요. 관심 신청은 결제나 예약 확정이 아니에요. 3명이 모이면 일정과 예상 경비를 먼저 안내드리고, 그때 정하시면 돼요.") +
      faq("날짜는 확정이에요?", "지금 날짜는 출발 후보일이에요. 신청하신 분들 일정에 맞춰 조정할 수 있어요.") +
      faq("누가 같이 가요?", "인생준준 세준이 함께 가요. 유적 앞에서 같이 읽고, 같이 걷고, 같이 먹는 여행을 만들어요.") + '</div>' +
      '<div class="credit">사진 · ' + esc(x.credit) + ' — 여행지를 이해하기 위한 자료 사진이에요.</div></div>' +
      '<div class="cta-bar"><button class="btn" data-apply="' + esc(x.id) + '">✈ ' + esc(x.country) + ' 관심 신청하기</button><small>결제 아님 · 이름과 연락처만 · 30초</small></div>';
    s.dataset.trip = x.id; s.hidden = false; s.scrollTop = 0; document.body.style.overflow = "hidden";
    reveal(s);
    try { history.pushState({ sheet: id }, ""); } catch (e) {}
  }
  /* 탑승권 사진이 그대로 커져 상세 화면 머리 사진이 되는 전환. 움직임 줄이기 설정이면 건너뜀 */
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var EASE = "cubic-bezier(.2,.9,.25,1)";
  function ghost(img, r, radius) {
    var g = document.createElement("div"); g.className = "morph-ghost"; g.setAttribute("aria-hidden", "true");
    g.style.cssText = "left:" + r.left + "px;top:" + r.top + "px;width:" + r.width + "px;height:" + r.height + "px;border-radius:" + radius + ";background-image:" + img;
    document.body.appendChild(g); return g;
  }
  function morphIn(fromEl) {
    var s = $("#sheet"), hero = $(".d-hero", s);
    if (calm || !fromEl || !hero || !s.animate) return;
    var a = fromEl.getBoundingClientRect(), b = hero.getBoundingClientRect();
    if (!a.width || a.bottom < 0 || a.top > innerHeight) return;
    s.classList.add("morphing");
    var g = ghost(getComputedStyle(fromEl).backgroundImage, a, "18px");
    s.animate([{ backgroundColor: "rgba(255,250,240,0)" }, { backgroundColor: "rgba(255,250,240,1)" }], { duration: 300, easing: "ease-out" });
    g.animate([
      { left: a.left + "px", top: a.top + "px", width: a.width + "px", height: a.height + "px", borderRadius: "18px" },
      { left: b.left + "px", top: b.top + "px", width: b.width + "px", height: b.height + "px", borderRadius: "0 0 32px 32px" }
    ], { duration: 460, easing: EASE, fill: "forwards" }).onfinish = function () { s.classList.remove("morphing"); g.remove(); };
  }
  function morphOut(done) {
    var s = $("#sheet"), hero = $(".d-hero", s), id = s.dataset.trip;
    var to = id && $('.pass[data-trip="' + id + '"] .pass-img');
    if (calm || !hero || !to || !s.animate || s.scrollTop > 40) return done();
    var a = hero.getBoundingClientRect(), b = to.getBoundingClientRect();
    if (b.bottom < 0 || b.top > innerHeight) return done();
    var g = ghost(getComputedStyle(hero).backgroundImage, a, "0 0 32px 32px");
    s.classList.add("morphing"); done();
    g.animate([
      { left: a.left + "px", top: a.top + "px", width: a.width + "px", height: a.height + "px", borderRadius: "0 0 32px 32px" },
      { left: b.left + "px", top: b.top + "px", width: b.width + "px", height: b.height + "px", borderRadius: "18px" }
    ], { duration: 380, easing: EASE, fill: "forwards" }).onfinish = function () { g.remove(); };
  }
  function faq(q, a) { return '<details><summary>' + esc(q) + '</summary><p>' + esc(a) + '</p></details>'; }
  function closeSheet() {
    var s = $("#sheet");
    morphOut(function () { s.hidden = true; s.innerHTML = ""; s.classList.remove("morphing"); delete s.dataset.trip; document.body.style.overflow = ""; });
  }

  function openApply(id) {
    var x = (DATA.trips || []).filter(function (t) { return t.id === id; })[0]; if (!x) return;
    var s = $("#sheet"); var saved = store.get("me", {});
    delete s.dataset.trip;
    s.innerHTML = '<button class="close" data-close aria-label="닫기">✕</button><div class="d-body" style="padding-top:calc(var(--st) + 58px)">' + GATE +
      '<div class="eyebrow chip">' + x.flag + ' ' + esc(x.country) + ' · ' + esc(x.dates) + '</div>' +
      '<h2 class="h1">' + esc(x.country) + ', 같이 갈래요?</h2><p class="lede">이름과 연락처만 남겨주세요. 3명이 모이면 일정과 예상 경비를 먼저 보내드려요.</p>' +
      '<form class="form" id="applyForm" novalidate>' +
      '<div class="field"><label for="fName">이름 또는 닉네임</label><input id="fName" autocomplete="name" maxlength="40" value="' + esc(saved.name || "") + '"></div>' +
      '<div class="field"><label for="fContact">연락처 (이메일 또는 카카오톡 ID)</label><input id="fContact" autocomplete="email" maxlength="80" inputmode="email" value="' + esc(saved.contact || "") + '"></div>' +
      '<label class="consent"><input type="checkbox" id="fConsent"><span>연락을 위해 이름·연락처를 인생준준 운영자 메일로 받는 데 동의해요. 여행 안내 외에는 쓰지 않아요. <a href="#" data-url="' + PRIVACY + '">개인정보 처리 안내</a></span></label>' +
      '<div class="err" id="fErr" role="alert"></div>' +
      '<button class="btn" id="fSend" type="submit">관심 신청 보내기</button></form></div>';
    s.hidden = false; s.scrollTop = 0;
    $("#applyForm").addEventListener("submit", function (e) { e.preventDefault(); send(x); });
  }
  function send(x) {
    var name = $("#fName").value.trim(), contact = $("#fContact").value.trim(), err = $("#fErr");
    if (!name) { err.textContent = "이름이나 닉네임을 적어주세요."; $("#fName").focus(); return; }
    if (contact.length < 3) { err.textContent = "답장 받을 이메일이나 카카오톡 ID를 적어주세요."; $("#fContact").focus(); return; }
    if (!$("#fConsent").checked) { err.textContent = "연락을 위한 동의에 체크해 주세요."; return; }
    err.textContent = ""; store.set("me", { name: name, contact: contact });
    var btn = $("#fSend"); btn.disabled = true; btn.textContent = "보내는 중…";
    var gate = $(".gate"); if (gate) gate.classList.add("go");
    var data = { _subject: "[인생준준 앱 관심 신청] " + x.country + " · " + name, _template: "box", _captcha: "false", 브랜드: "인생준준 " + (OS === "android" ? "안드로이드" : "iOS") + " 앱", 관심여행: x.country + " (" + x.dates + ")", 이름: name, 연락처: contact, 유입: OS + "-app", 동의: "예 (연락 목적)" };
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)) data._replyto = contact;
    var done = false;
    var timer = setTimeout(function () { if (!done) { done = true; result(x, false, name, contact); } }, 15000);
    fetch("https://formsubmit.co/ajax/" + MAIL, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) { if (done) return; done = true; clearTimeout(timer); result(x, j && (j.success === true || j.success === "true"), name, contact); })
      .catch(function () { if (done) return; done = true; clearTimeout(timer); result(x, false, name, contact); });
  }
  function result(x, ok, name, contact) {
    var s = $("#sheet");
    if (!ok) { var gate = $(".gate"); if (gate) gate.classList.remove("go"); }
    var text = "[인생준준 · " + x.country + " 관심 신청]\n이름: " + name + "\n연락처: " + contact;
    if (ok) {
      haptic("ok");
      var applied = store.get("applied", []); if (applied.indexOf(x.id) < 0) applied.push(x.id); store.set("applied", applied);
      s.innerHTML = '<div class="confetti" aria-hidden="true">' + confetti() + '</div><button class="close" data-close aria-label="닫기">✕</button><div class="d-body done" style="padding-top:calc(var(--st) + 60px)"><div class="big-stamp">신청<br>완료</div>' +
        '<h2 class="h1">' + esc(x.country) + ' 탑승 대기 명단에 올렸어요</h2><p class="lede">24시간 안에 남겨주신 연락처로 연락드릴게요. 새 여행 소식은 카카오톡 공지방에서 먼저 받아보세요.</p>' +
        '<div class="alt"><button class="btn" data-url="' + KAKAO + '">💬 카카오톡 공지방</button><button class="btn ghost" data-close>확인</button></div></div>';
    } else {
      s.innerHTML = '<button class="close" data-close aria-label="닫기">✕</button><div class="d-body done" style="padding-top:calc(var(--st) + 60px)">' +
        '<h2 class="h1">지금은 자동 접수가 안 됐어요</h2><p class="lede">아래 중 편한 곳으로 한 줄만 보내주세요. 신청 내용을 복사해 둘게요.</p>' +
        '<div class="alt"><button class="btn" data-copy="' + esc(text) + '" data-url="' + KAKAO + '">💬 카카오톡으로 보내기</button>' +
        '<button class="btn ghost" data-copy="' + esc(text) + '" data-url="' + INSTA + '">📸 인스타 DM으로 보내기</button>' +
        '<p class="fine">이메일: <b style="user-select:text;-webkit-user-select:text">' + MAIL + '</b></p></div></div>';
    }
    s.scrollTop = 0;
  }

  /* 신청 화면 위 손그림: 언덕 위 활주로에서 기다리는 작은 비행기, 펄럭이는 바람자루, 흘러가는 구름 */
  var GATE = '<div class="gate" aria-hidden="true"><svg viewBox="0 0 400 120" preserveAspectRatio="xMidYMid slice">' +
    '<defs><linearGradient id="gSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fd6fb"/><stop offset="1" stop-color="#e6f6ff"/></linearGradient>' +
    '<linearGradient id="gHill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b6e48a"/><stop offset="1" stop-color="#86cc6c"/></linearGradient></defs>' +
    '<rect width="400" height="120" fill="url(#gSky)"/>' +
    '<g class="g-sun"><circle cx="338" cy="30" r="26" fill="#ffe28a" opacity=".45"/><circle cx="338" cy="30" r="12" fill="#fff4b8"/></g>' +
    '<g class="g-cloud c1" fill="#fff"><circle cx="70" cy="32" r="11"/><circle cx="85" cy="26" r="14"/><circle cx="101" cy="32" r="10"/><rect x="62" y="31" width="46" height="10" rx="5"/></g>' +
    '<g class="g-cloud c2" fill="#fff" opacity=".85"><circle cx="230" cy="22" r="8"/><circle cx="241" cy="17" r="10"/><circle cx="253" cy="23" r="7"/><rect x="224" y="22" width="34" height="7" rx="3.5"/></g>' +
    '<path d="M0 78 C50 60 100 70 150 64 C210 56 260 72 310 62 C350 55 380 60 400 64 V120 H0Z" fill="#8fd27a"/>' +
    '<g fill="#4f9f63"><circle cx="30" cy="70" r="7"/><circle cx="40" cy="66" r="9"/><circle cx="50" cy="71" r="6"/></g>' +
    '<path d="M0 96 C80 84 170 90 240 86 C310 82 360 90 400 88 V120 H0Z" fill="url(#gHill)"/>' +
    '<path d="M60 104 C150 98 250 96 360 90" fill="none" stroke="#f3e2b8" stroke-width="9" stroke-linecap="round"/>' +
    '<path d="M60 104 C150 98 250 96 360 90" fill="none" stroke="#fff" stroke-width="1.6" stroke-dasharray="6 8" stroke-linecap="round" opacity=".9"/>' +
    '<g transform="translate(322 66)"><rect x="-1" y="0" width="2" height="24" fill="#8b5e3c"/><path class="g-sock" d="M1 1 L19 3.5 L19 7.5 L1 9Z" fill="#ff8a6b"/><path d="M7 1.8 V8.2 M13 2.7 V7.8" stroke="#fff" stroke-width="2"/></g>' +
    '<g transform="translate(352 72)"><rect x="-8" y="0" width="16" height="13" fill="#fff8ec"/><path d="M-11 2 L0 -8 L11 2Z" fill="#e5634f"/><rect x="-3" y="6" width="5" height="7" fill="#8b5e3c"/></g>' +
    '<g class="g-plane"><g class="g-bob"><path d="M-17 0 C-17 -4 -12 -5 -6 -5 L12 -4.5 C17 -4.3 20 -2 20 0 C20 2 17 3.6 12 3.8 L-6 4 C-12 4 -17 3 -17 0Z" fill="#fff" stroke="#2f6f55" stroke-width="1.4"/>' +
    '<path d="M-2 0 L-9 -12 L-4 -12 L6 -1Z" fill="#ff8a6b" stroke="#2f6f55" stroke-width="1.2" stroke-linejoin="round"/><path d="M-15 -2 L-19 -11 L-15 -11 L-10 -3Z" fill="#ff8a6b" stroke="#2f6f55" stroke-width="1.2" stroke-linejoin="round"/>' +
    '<g fill="#5fb3e6"><circle cx="2" cy="-1" r="1.4"/><circle cx="6.5" cy="-1" r="1.4"/><circle cx="11" cy="-1" r="1.4"/></g><path d="M15.5 -3 C18 -2.5 19 -1.4 19 -.5 L15.5 -.6Z" fill="#5fb3e6"/>' +
    '<g fill="#2f6f55"><circle cx="-6" cy="6.5" r="1.8"/><circle cx="10" cy="6.5" r="1.8"/></g></g></g>' +
    '</svg></div>';

  function confetti() {
    var c = ["#ff8a6b", "#ffd46a", "#9fd67f", "#5fb3e6", "#b7a6f2", "#f58eaa"], out = "";
    for (var i = 0; i < 36; i++) out += '<i style="left:' + ((i * 37) % 100) + '%;background:' + c[i % c.length] + ';animation-delay:' + ((i % 9) * 0.08).toFixed(2) + 's;--dx:' + (((i * 53) % 60) - 30) + 'px;--rot:' + ((i * 97) % 360) + 'deg"></i>';
    return out;
  }

  /* 화면에 들어올 때 살짝 떠오르기 */
  var io = window.IntersectionObserver ? new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -8% 0px" }) : null;
  function reveal(root) {
    if (!io) return;
    Array.prototype.forEach.call((root || document).querySelectorAll(".pass,.tcard,.see>div,.flow li,.link,.about"), function (el, i) { el.classList.add("rv"); el.style.setProperty("--d", (Math.min(i, 8) * 40) + "ms"); io.observe(el); });
  }

  /* ── 여행 카드 ── */
  function viewCards() {
    var cards = DATA.cards || [], saved = store.get("saved", []);
    var places = ["전체", "저장"].concat(cards.map(function (c) { return c.place; }).filter(function (p, i, a) { return a.indexOf(p) === i; }));
    var list = cards.filter(function (c) { return state.cardFilter === "전체" || (state.cardFilter === "저장" ? saved.indexOf(c.id) > -1 : c.place === state.cardFilter); });
    return '<div class="banner"><img src="img/cards.svg" alt=""></div><h1 class="h1">가기 전에 알면<br>덜 당황하는 것들</h1><p class="lede">나라별 매너·벌금·꿀팁 카드예요. 인터넷이 없어도 열려요. ♥ 를 누르면 저장돼요.</p>' +
      '<div class="filters" role="tablist">' + places.map(function (p) { return '<button role="tab" data-filter="' + esc(p) + '" class="' + (p === state.cardFilter ? "on" : "") + '">' + (p === "저장" ? "♥ 저장 " + saved.length : esc(p)) + '</button>'; }).join("") + '</div>' +
      (list.length ? '<div class="tcards">' + list.map(function (c) {
        var on = saved.indexOf(c.id) > -1;
        return '<article class="tcard" style="--g1:' + c.grad[0] + ';--g2:' + c.grad[1] + '"><div class="tcard-top"><div class="row"><span class="flag">' + c.flag + '</span><span class="place">' + esc(c.place) + '</span><span class="kind">' + esc(c.kind) + '</span></div><h3>' + esc(c.title) + '</h3></div>' +
          '<ul>' + c.points.map(function (p) { return '<li>' + esc(p) + '</li>'; }).join("") + '</ul>' +
          '<div class="tcard-foot"><small>출처 · ' + esc(c.source) + '</small><button class="save' + (on ? " on" : "") + '" data-save="' + esc(c.id) + '" aria-pressed="' + on + '" aria-label="카드 저장">' + (on ? "♥" : "♡") + '</button></div></article>';
      }).join("") + '</div>' : '<div class="empty">아직 저장한 카드가 없어요.<br>마음에 드는 카드의 ♡ 를 눌러 보세요.</div>') +
      '<p class="fine">규정·벌금은 바뀔 수 있어요. 출발 전에 현지 공식 안내를 한 번 더 확인하세요.</p>';
  }

  /* ── 내 여권 ── */
  function viewPassport() {
    var visited = store.get("visited", {}), wish = store.get("wish", []);
    var codes = Object.keys(visited).filter(function (k) { return CTY[k]; }).sort(function (a, b) { return visited[a] < visited[b] ? -1 : 1; });
    var regions = codes.map(function (k) { return CTY[k].region; }).filter(function (r, i, a) { return a.indexOf(r) === i; });
    return '<div class="banner"><img src="img/passport.svg" alt=""></div><section class="pp-cover"><div class="t">PASSPORT · 여권</div><h2>나의 여행 여권</h2><div style="font-size:13px;color:#e7d9aa">다녀온 나라를 눌러 도장을 찍어요</div><div class="emb" aria-hidden="true">🧭</div>' +
      '<div class="stats"><div><b>' + codes.length + '</b><span>다녀온 나라</span></div><div><b>' + regions.length + '</b><span>지역</span></div><div><b>' + wish.length + '</b><span>가고 싶은 곳</span></div></div></section>' +
      '<div class="page"><h4>VISAS · 도장</h4><div class="stamps">' + (codes.length ? codes.map(function (k, i) {
        var c = CTY[k], d = visited[k];
        return '<div class="stamp' + (state.fresh === k ? " new" : "") + '" style="--c:' + c.color + ';--rot:' + (((i * 37) % 21) - 10) + 'deg"><div><span class="f">' + c.flag + '</span><span class="n">' + esc(c.name) + '</span><span class="d">' + esc(d.replace(/-/g, ".")) + '</span></div></div>';
      }).join("") : '<div class="empty">아직 도장이 없어요.<br>아래에서 다녀온 나라를 눌러 보세요.</div>') + '</div></div>' +
      '<div class="seg" role="tablist"><button role="tab" data-mode="visit" class="' + (state.mode === "visit" ? "on" : "") + '">🛂 다녀온 곳</button><button role="tab" data-mode="wish" class="' + (state.mode === "wish" ? "on" : "") + '">♥ 가고 싶은 곳</button></div>' +
      '<div class="seg-hint">' + (state.mode === "visit" ? "누르면 도장이 찍혀요. 한 번 더 누르면 지워져요." : "누르면 가고 싶은 곳에 담겨요. 같이 갈 여행이 생기면 먼저 알려드릴게요.") + '</div>' +
      REGIONS.map(function (r) {
        return '<div class="region" style="--rc:' + r[1] + '"><h5><i></i>' + esc(r[0]) + '</h5><div class="countries">' + r[2].map(function (c) {
          var v = !!visited[c[0]], w = wish.indexOf(c[0]) > -1;
          return '<button class="cty' + (v ? " v" : "") + (w ? " w" : "") + '" data-cty="' + c[0] + '" aria-pressed="' + (state.mode === "visit" ? v : w) + '"><span class="f">' + c[2] + '</span>' + esc(c[1]) + (v ? '<span class="mark">✓</span>' : w ? '<span class="mark">♥</span>' : "") + '</button>';
        }).join("") + '</div></div>';
      }).join("") +
      '<p class="fine">여권 기록은 이 휴대폰 안에만 저장돼요. 서버로 보내지 않아요.</p>';
  }
  function toggleCountry(code) {
    var c = CTY[code]; if (!c) return;
    if (state.mode === "visit") {
      var visited = store.get("visited", {});
      if (visited[code]) { delete visited[code]; state.fresh = null; toast(c.flag + " " + c.name + " 도장을 지웠어요"); }
      else { visited[code] = new Date(Date.now() + 324e5).toISOString().slice(0, 10); state.fresh = code; haptic("heavy"); toast(c.flag + " " + c.name + " 도장 쾅!"); }
      store.set("visited", visited);
    } else {
      var wish = store.get("wish", []), i = wish.indexOf(code);
      if (i > -1) wish.splice(i, 1); else { wish.push(code); haptic(); toast("♥ " + c.name + " 가고 싶은 곳에 담았어요"); }
      store.set("wish", wish);
    }
    var y = window.scrollY; render(true); window.scrollTo(0, y);
  }

  /* ── 라운지 ── */
  function viewLounge() {
    function L(icon, bg, t, s, url) { return '<button class="link" data-url="' + url + '"><span class="ic" style="--bg:' + bg + '">' + icon + '</span><span><b>' + t + '</b><small>' + s + '</small></span><span class="arr">↗</span></button>'; }
    return '<div class="banner"><img src="img/lounge.svg" alt=""></div><h1 class="h1">라운지</h1><p class="lede">새 여행 소식과 여행 이야기는 여기서 먼저 만나요.</p>' +
      '<div class="links">' +
      L("💬", "linear-gradient(135deg,#fee500,#f5b400)", "카카오톡 공지방", "새 여행·출발 소식을 먼저 받아요", KAKAO) +
      L("📸", "linear-gradient(135deg,#f58529,#dd2a7b,#8134af)", "인스타그램 @lifejunjun", "매일 올라오는 여행 릴스", INSTA) +
      L("▶️", "linear-gradient(135deg,#ff4e45,#c4302b)", "유튜브 인생준준", "여행 영상과 쇼츠", YT) +
      L("🗺️", "linear-gradient(135deg,#00d2b4,#2f80ed)", "여행 웹사이트", "전체 여행과 칼럼", SITE) +
      '</div>' +
      '<div class="sec-t">인생준준은</div><div class="card"><p class="d-p" style="margin:0">혼자 떠나긴 조금 무섭고, 40명 단체 패키지는 싫은 사람들이 3~10명으로 함께 가는 역사 여행이에요. 먼저 공부해 온 길동무와 유적 앞에서 같이 읽고, 같이 걷고, 같이 먹어요. 쇼핑·옵션 강요는 없어요.</p></div>' +
      '<div class="links" style="margin-top:14px">' + L("🔒", "linear-gradient(135deg,#5a6fb0,#9b5de5)", "개인정보 처리 안내", "관심 신청 때 받은 이름·연락처는 연락에만 써요", PRIVACY) + '</div>' +
      '<p class="fine">인생준준 앱 ' + VERSION + '<br>문의 · ' + MAIL + '<br>여행 사진 · Unsplash (각 여행 화면에 작가 표기) · 글꼴 · Pretendard, Black Han Sans (SIL Open Font License)</p>';
  }

  /* ── 이벤트 ── */
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-tab],[data-trip],[data-apply],[data-close],[data-url],[data-filter],[data-save],[data-mode],[data-cty]");
    if (!t) return;
    if (t.dataset.tab) { if (t.dataset.tab !== state.tab) haptic(); return setTab(t.dataset.tab); }
    if (t.dataset.trip) { haptic(); openTrip(t.dataset.trip); return morphIn(t.querySelector(".pass-img")); }
    if (t.dataset.apply) return openApply(t.dataset.apply);
    if (t.hasAttribute("data-close")) { e.preventDefault(); return closeSheet(); }
    if (t.dataset.url) {
      e.preventDefault();
      if (t.dataset.copy && navigator.clipboard) navigator.clipboard.writeText(t.dataset.copy).then(function () { toast("신청 내용을 복사했어요"); }).catch(function () {});
      return openUrl(t.dataset.url);
    }
    if (t.dataset.filter) { state.cardFilter = t.dataset.filter; return render(); }
    if (t.dataset.save) {
      var saved = store.get("saved", []), i = saved.indexOf(t.dataset.save);
      if (i > -1) saved.splice(i, 1); else { saved.push(t.dataset.save); haptic(); toast("♥ 카드를 저장했어요"); }
      store.set("saved", saved); var y = window.scrollY; render(true); window.scrollTo(0, y); return;
    }
    if (t.dataset.mode) { state.mode = t.dataset.mode; var y2 = window.scrollY; render(true); window.scrollTo(0, y2); return; }
    if (t.dataset.cty) return toggleCountry(t.dataset.cty);
  });
  window.addEventListener("popstate", function () { if (!$("#sheet").hidden) closeSheet(); });
  try { if (P.App) P.App.addListener("backButton", function () {
    if (!$("#sheet").hidden) return closeSheet();
    if (state.tab !== "home") return setTab("home");
    P.App.exitApp();
  }); } catch (e) {}

  Promise.all([load("trips"), load("cards")]).then(function (r) {
    DATA.trips = r[0] || []; DATA.cards = r[1] || [];
    setTab(["home", "cards", "passport", "lounge"].indexOf(state.tab) > -1 ? state.tab : "home");
    try { if (P.SplashScreen) P.SplashScreen.hide(); } catch (e) {}
  }).catch(function () { setTab("home"); });
})();
