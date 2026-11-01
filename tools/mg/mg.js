// mg.js — tiny deterministic motion-graphics engine (no deps). Scenes register tweens; seek(t) sets every style for time t.
(function () {
  const E = {
    lin: x => x,
    out: x => 1 - Math.pow(1 - x, 3),
    out5: x => 1 - Math.pow(1 - x, 5),
    inOut: x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
    in: x => x * x * x,
    back: x => { const c = 1.9, c3 = c + 1; return 1 + c3 * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); },
    expo: x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x),
  };
  const DEF = { x: 0, y: 0, z: 0, scale: 1, scaleX: 1, scaleY: 1, rotate: 0, rotateX: 0, rotateY: 0, skewX: 0, opacity: 1, blur: 0, clipL: 0, clipR: 0, clipT: 0, clipB: 0, ls: null, bright: 1 };
  const tweens = []; const els = new Set();
  function list(t) { return typeof t === 'string' ? [...document.querySelectorAll(t)] : (Array.isArray(t) ? t.flatMap(list) : [t]); }
  // T(target, t0, dur, {prop:[from,to]}, ease, stagger)
  function T(target, t0, dur, props, ease = 'out', stagger = 0) {
    list(target).forEach((el, i) => { els.add(el); tweens.push({ el, t0: t0 + i * stagger, dur, props, ease: E[ease] || ease }); });
  }
  // set(target, t, {prop:value}) — instant
  function set(target, t, props) { const p = {}; for (const k in props) p[k] = [props[k], props[k]]; T(target, t, 0.0001, p, 'lin'); }
  function split(sel) {
    list(sel).forEach(el => {
      const txt = el.textContent; el.textContent = '';
      [...txt].forEach(ch => { const s = document.createElement('span'); s.className = 'ch'; s.textContent = ch === ' ' ? ' ' : ch; el.appendChild(s); });
    });
  }
  function seek(t) {
    for (const el of els) {
      const st = Object.assign({}, DEF, el.__base || {});
      for (const tw of tweens) {
        if (tw.el !== el || t < tw.t0) continue;
        const u = tw.dur <= 0 ? 1 : Math.min(1, (t - tw.t0) / tw.dur), e = tw.ease(u);
        for (const k in tw.props) { const [a, b] = tw.props[k]; st[k] = a + (b - a) * e; }
      }
      el.style.transform = `translate3d(${st.x}px,${st.y}px,${st.z}px) rotateX(${st.rotateX}deg) rotateY(${st.rotateY}deg) rotate(${st.rotate}deg) skewX(${st.skewX}deg) scale(${st.scale * st.scaleX},${st.scale * st.scaleY})`;
      el.style.opacity = st.opacity;
      el.style.filter = (st.blur > 0.05 ? `blur(${st.blur}px) ` : '') + (st.bright !== 1 ? `brightness(${st.bright})` : '');
      el.style.clipPath = `inset(${st.clipT}% ${st.clipR}% ${st.clipB}% ${st.clipL}%)`;
      if (st.ls !== null) el.style.letterSpacing = st.ls + 'px';
    }
    if (window.onSeek) window.onSeek(t);
  }
  // initial state = earliest tween "from" values for each element
  function init() {
    tweens.sort((a, b) => a.t0 - b.t0);
    for (const el of els) {
      const base = {}; const seen = {};
      tweens.filter(tw => tw.el === el).sort((a, b) => a.t0 - b.t0).forEach(tw => { for (const k in tw.props) if (!seen[k]) { seen[k] = 1; base[k] = tw.props[k][0]; } });
      el.__base = base;
    }
  }
  window.MG = { T, set, split, seek, init, E };
})();
