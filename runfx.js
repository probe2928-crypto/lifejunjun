/* RUN & TREK cinematic layer — intro film, course films, photo posters.
   Shared by run.html (인생준준) and a copy in the probe2928-crypto/yeobaek repo (여백의 지도).
   Page sets window.RUNFX = {brand, tagline, accent, ink, words:[...]} before loading. */
(function(){
  const CFG=Object.assign({brand:"RUN & TREK",tagline:"함께 달리고, 함께 걷는 세계.",accent:"#C8261C",ink:"#0b0b0b",
    words:["RUN.","CLIMB.","BREATHE.","TOGETHER."]},window.RUNFX||{});
  const reduce=()=>{try{return matchMedia("(prefers-reduced-motion: reduce)").matches;}catch(e){return false;}};

  // fonts + styles
  const f=document.createElement("link");f.rel="stylesheet";
  f.href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo+Black&family=Bodoni+Moda:ital,wght@0,400;0,600;1,400&family=Cormorant+Garamond:ital,wght@0,300;1,300&display=swap";document.head.append(f);
  const css=`
  .fx-film{position:fixed;inset:0;z-index:9999;background:#000;color:#fff;overflow:hidden;opacity:0;transition:opacity .35s ease}
  .fx-film.on{opacity:1}.fx-film.out{opacity:0;transition:opacity .6s ease}
  .fx-scene{position:absolute;inset:0;opacity:0}
  .fx-scene.on{opacity:1}
  .fx-img{position:absolute;inset:-4%;background-size:cover;background-position:center;will-change:transform;filter:saturate(1.05) contrast(1.08)}
  .fx-scene.on .fx-img{animation:fxkb var(--d,1800ms) cubic-bezier(.2,.6,.2,1) forwards}
  .fx-scene.alt.on .fx-img{animation-name:fxkb2}
  @keyframes fxkb{from{transform:scale(1.22) translate3d(-2%,1%,0)}to{transform:scale(1.04) translate3d(1%,-1%,0)}}
  @keyframes fxkb2{from{transform:scale(1.04) translate3d(2%,-1%,0)}to{transform:scale(1.2) translate3d(-1%,1%,0)}}
  .fx-scene.dark .fx-shade{background:radial-gradient(ellipse at center,rgba(0,0,0,.55),rgba(0,0,0,.35) 70%)}
  .fx-shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,.05) 35%,rgba(0,0,0,.55) 100%)}
  .fx-grain{position:absolute;inset:-50%;pointer-events:none;opacity:.14;mix-blend-mode:overlay;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
    animation:fxgrain .6s steps(4) infinite}
  @keyframes fxgrain{0%{transform:translate(0,0)}25%{transform:translate(-3%,2%)}50%{transform:translate(2%,-3%)}75%{transform:translate(-2%,-1%)}}
  .fx-bars:before,.fx-bars:after{content:"";position:absolute;left:0;right:0;height:7vh;background:#000;z-index:5}
  .fx-bars:before{top:0}.fx-bars:after{bottom:0}
  .fx-speed{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:2}
  .fx-speed i{position:absolute;height:2px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.85),transparent);animation:fxstreak .7s linear infinite;opacity:.0}
  .fx-scene.on .fx-speed i{opacity:.55}
  @keyframes fxstreak{from{transform:translateX(-30vw)}to{transform:translateX(130vw)}}
  .fx-txt{position:absolute;z-index:4;left:6vw;right:6vw;bottom:15vh;display:flex;flex-direction:column;gap:1.4vh}
  .fx-txt.center{top:0;bottom:0;justify-content:center;align-items:center;text-align:center}
  .fx-big{font-family:Anton,"Archivo Black",Impact,"Noto Sans KR",sans-serif;font-size:clamp(64px,15vw,230px);line-height:.86;letter-spacing:-.01em;text-transform:uppercase;margin:0}
  .fx-scene.on .fx-big{animation:fxslam .55s cubic-bezier(.15,.9,.2,1) both}
  @keyframes fxslam{0%{transform:scale(1.45);opacity:0;filter:blur(14px);letter-spacing:.2em}60%{opacity:1}100%{transform:scale(1);filter:blur(0);letter-spacing:-.01em}}
  .fx-big em{font-style:normal;color:var(--fx-accent)}
  .fx-mid{font-family:Anton,"Archivo Black",Impact,sans-serif;font-size:clamp(40px,8vw,120px);line-height:.9;text-transform:uppercase}
  .fx-small{font-family:"Noto Sans KR",sans-serif;font-weight:700;font-size:clamp(15px,1.8vw,24px);letter-spacing:-.02em;opacity:0}
  .fx-scene.on .fx-small{animation:fxup .6s .25s cubic-bezier(.2,.8,.2,1) forwards}
  @keyframes fxup{from{opacity:0;transform:translateY(18px)}to{opacity:.95;transform:none}}
  .fx-tag{display:inline-block;align-self:flex-start;background:var(--fx-accent);color:var(--fx-on-accent);font:800 12px/1 "Noto Sans KR",sans-serif;letter-spacing:.16em;padding:8px 12px;text-transform:uppercase}
  .fx-txt.center .fx-tag{align-self:center}
  .fx-corner{position:absolute;z-index:6;top:calc(7vh + 18px);left:6vw;right:6vw;display:flex;justify-content:space-between;font:600 11px/1.4 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.18em;text-transform:uppercase;opacity:.85}
  .fx-credit{position:absolute;z-index:6;right:6vw;bottom:calc(7vh + 10px);font:500 10px/1.3 ui-monospace,Menlo,monospace;opacity:.6;max-width:60vw;text-align:right}
  .fx-snd{position:absolute;z-index:8;left:20px;top:calc(7vh + 50px);appearance:none;border:1px solid rgba(255,255,255,.6);background:rgba(0,0,0,.25);color:#fff;font:700 12px "Noto Sans KR",sans-serif;letter-spacing:.08em;padding:10px 16px;border-radius:99px;cursor:pointer;backdrop-filter:blur(6px);display:inline-flex;align-items:center;gap:8px}
  .fx-snd .eq{display:inline-flex;gap:2px;align-items:flex-end;height:11px}.fx-snd .eq i{width:2px;background:currentColor;height:30%;animation:fxeq .9s ease-in-out infinite}.fx-snd .eq i:nth-child(2){animation-delay:-.3s}.fx-snd .eq i:nth-child(3){animation-delay:-.6s}
  .fx-snd.off .eq i{animation:none;height:2px}
  @keyframes fxeq{0%,100%{height:25%}50%{height:100%}}
  .fx-mcredit{position:absolute;z-index:6;left:6vw;bottom:calc(7vh + 10px);font:500 10px/1.3 ui-monospace,Menlo,monospace;opacity:.6;max-width:40vw}
  .fx-prog{position:absolute;z-index:7;top:0;left:0;height:3px;background:var(--fx-accent);width:0}
  .fx-skip{position:absolute;z-index:8;right:20px;top:calc(7vh + 50px);appearance:none;border:1px solid rgba(255,255,255,.6);background:rgba(0,0,0,.25);color:#fff;font:700 12px "Noto Sans KR",sans-serif;letter-spacing:.08em;padding:10px 16px;border-radius:99px;cursor:pointer;backdrop-filter:blur(6px)}
  .fx-skip:hover{background:#fff;color:#000}
  .fx-flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:3;pointer-events:none}
  .fx-scene.on .fx-flash{animation:fxflash .35s ease-out}
  @keyframes fxflash{0%{opacity:.55}100%{opacity:0}}
  .fx-count{font-variant-numeric:tabular-nums}

  /* LUXE preset — slow, monochrome, serif, crossfades */
  .fx-film.luxe .fx-scene{transition:opacity 1.1s ease}
  .fx-film.luxe .fx-img{filter:grayscale(1) contrast(1.18) brightness(.92)}
  .fx-film.luxe .fx-scene.color .fx-img{filter:saturate(.75) contrast(1.1) brightness(.9)}
  .fx-film.luxe .fx-scene.on .fx-img{animation:fxlux var(--d,2600ms) linear forwards}
  @keyframes fxlux{from{transform:scale(1.12)}to{transform:scale(1.0)}}
  .fx-film.luxe .fx-shade{background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.1) 40%,rgba(0,0,0,.6))}
  .fx-film.luxe .fx-big{font-family:"Bodoni Moda",Didot,"Times New Roman",serif;font-weight:400;font-style:italic;text-transform:none;font-size:clamp(46px,9vw,140px);letter-spacing:-.02em;line-height:1}
  .fx-film.luxe .fx-scene.on .fx-big{animation:fxluxin 1.6s cubic-bezier(.2,.7,.1,1) both}
  @keyframes fxluxin{from{opacity:0;letter-spacing:.12em;filter:blur(6px)}to{opacity:1;letter-spacing:-.02em;filter:blur(0)}}
  .fx-film.luxe .fx-mid{font-family:"Bodoni Moda",Didot,serif;font-weight:400;text-transform:none;font-size:clamp(36px,6vw,92px)}
  .fx-film.luxe .fx-small{font-family:"Cormorant Garamond","Noto Serif KR",serif;font-weight:300;font-size:clamp(16px,1.7vw,24px);letter-spacing:.06em}
  .fx-film.luxe .fx-scene.on .fx-small{animation:fxup 1.2s .6s ease forwards}
  .fx-film.luxe .fx-tag{background:transparent;color:#fff;border-top:1px solid rgba(255,255,255,.7);border-bottom:1px solid rgba(255,255,255,.7);padding:9px 2px;letter-spacing:.42em;font-weight:500;font-size:11px}
  .fx-film.luxe .fx-corner{letter-spacing:.42em;font-weight:400;opacity:.7}
  .fx-film.luxe .fx-flash,.fx-film.luxe .fx-speed{display:none}
  .fx-film.luxe.fx-bars:before,.fx-film.luxe.fx-bars:after{height:11vh}
  .fx-film.luxe .fx-prog{background:#fff;height:1px}
  .fx-film.luxe .fx-grain{opacity:.2}
  .fx-reel{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
  .fx-reel button{appearance:none;cursor:pointer;border:1px solid currentColor;background:transparent;color:inherit;border-radius:99px;padding:8px 14px;font:600 12px "Noto Sans KR",sans-serif;opacity:.85}
  .fx-reel button:hover{opacity:1;background:rgba(127,127,127,.12)}
  .fx-reel small{opacity:.6;margin-left:6px;font-weight:500}
  .fx-play{display:inline-flex;align-items:center;gap:10px;appearance:none;border:0;cursor:pointer;background:#000;color:#fff;font:800 13px "Noto Sans KR",sans-serif;letter-spacing:.12em;padding:12px 18px 12px 14px;border-radius:99px;text-transform:uppercase}
  .fx-play b{width:26px;height:26px;border-radius:50%;background:var(--fx-accent);display:grid;place-items:center;font-size:10px;color:var(--fx-on-accent)}
  .fx-play:hover{transform:translateY(-1px)}
  .fx-play.light{background:rgba(255,255,255,.14);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.5)}
  .fx-photo{position:absolute;inset:0;background-size:cover;background-position:center;transition:transform 1.2s cubic-bezier(.2,.7,.2,1)}
  .fx-tint{position:absolute;inset:0}
  .fx-photo,.fx-tint{position:absolute!important;inset:0!important;z-index:0!important}
  a:hover .fx-photo{transform:scale(1.07)}
  .fx-gal{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
  @media (max-width:700px){.fx-gal{grid-template-columns:minmax(0,1fr)}}
  .fx-gal figure{margin:0;position:relative;overflow:hidden;aspect-ratio:4/3;background:#111}
  .fx-gal img{width:100%;height:100%;object-fit:cover;transition:transform 1.2s cubic-bezier(.2,.7,.2,1);display:block}
  .fx-gal figure:hover img{transform:scale(1.06)}
  .fx-gal figcaption{position:absolute;left:0;right:0;bottom:0;padding:28px 12px 10px;background:linear-gradient(transparent,rgba(0,0,0,.75));color:#fff;font-size:12.5px;line-height:1.45}
  .fx-gal figcaption a{display:block;opacity:.75;font-size:10.5px;margin-top:2px;text-decoration:underline}
  `;
  const st=document.createElement("style");st.textContent=css;document.head.append(st);
  document.documentElement.style.setProperty("--fx-accent",CFG.accent);
  document.documentElement.style.setProperty("--fx-on-accent",CFG.onAccent||"#fff");

  const h=(tag,cls,html)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e;};
  const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  function preload(urls){return Promise.all(urls.filter(Boolean).map(u=>new Promise(r=>{const i=new Image();i.onload=i.onerror=()=>r();i.src=u;setTimeout(r,2500);})));}

  let active=null;
  // 필름 음악: Wikimedia Commons 자유 라이선스 곡을 스트리밍, 페이드 인·아웃
  const DEFAULT_MUSIC={src:"https://upload.wikimedia.org/wikipedia/commons/transcoded/1/11/Scott_Buckley_-_Pathfinder.oga/Scott_Buckley_-_Pathfinder.oga.mp3",start:150,credit:"Scott Buckley — Pathfinder (CC BY 4.0)"};
  const soundPref={get(){try{return localStorage.getItem("fx-sound")!=="off";}catch(e){return true;}},set(v){try{localStorage.setItem("fx-sound",v?"on":"off");}catch(e){}}};
  function makeSound(m){
    const a=new Audio();a.crossOrigin="anonymous";a.preload="auto";a.src=m.src+(m.start?"#t="+m.start:"");
    let ctx=null,g=null;
    try{const AC=window.AudioContext||window.webkitAudioContext;if(AC){ctx=new AC();g=ctx.createGain();g.gain.value=0;ctx.createMediaElementSource(a).connect(g).connect(ctx.destination);}}catch(e){ctx=null;g=null;}
    if(!g)a.volume=0;
    let fadeT=null;
    function fade(v,sec){if(g){const t=ctx.currentTime;g.gain.cancelScheduledValues(t);g.gain.setValueAtTime(g.gain.value,t);g.gain.linearRampToValueAtTime(v,t+sec);return;}
      clearInterval(fadeT);const from=a.volume,t0=performance.now();fadeT=setInterval(()=>{const k=Math.min(1,(performance.now()-t0)/(sec*1000));try{a.volume=from+(v-from)*k;}catch(e){}if(k>=1)clearInterval(fadeT);},40);}
    let on=false;
    return{
      play(offset){if(ctx&&ctx.state==="suspended")ctx.resume().catch(()=>{});
        if(offset&&a.readyState>0){try{a.currentTime=(m.start||0)+offset;}catch(e){}}
        return a.play().then(()=>{on=true;fade(.85,1.4);return true;}).catch(()=>false);},
      pause(){on=false;fade(0,.4);setTimeout(()=>{if(!on)a.pause();},450);},
      stop(){on=false;fade(0,.7);setTimeout(()=>{a.pause();a.removeAttribute("src");try{a.load();}catch(e){}if(ctx)ctx.close().catch(()=>{});},800);},
      get on(){return on;}
    };
  }
  // 사진 주소가 깨져도 검은 화면이 되지 않도록: 실패한 장면은 검증된 대회 사진(POOL)으로 대체
  let POOL=[];let poolIdx=0;
  function setPool(races){const u=(races||[]).flatMap(r=>(r.photos||[]).map(p=>p&&p.src)).filter(Boolean);if(u.length)POOL=u;}
  function check(u){return new Promise(r=>{if(!u)return r(false);const i=new Image();const t=setTimeout(()=>r(true),6000);i.onload=()=>{clearTimeout(t);r(true);};i.onerror=()=>{clearTimeout(t);r(false);};i.src=u;});}
  function nextPool(){if(!POOL.length)return null;const u=POOL[poolIdx%POOL.length];poolIdx+=3;return u;}
  function film(scenes,opts={}){
    if(reduce()||!scenes.length)return Promise.resolve();
    if(active)active.stop();
    return new Promise(async resolve=>{
      const root=h("div","fx-film fx-bars"+(opts.style==="luxe"?" luxe":""));root.setAttribute("role","dialog");root.setAttribute("aria-label",opts.label||"소개 영상");
      const prog=h("div","fx-prog");const skip=h("button","fx-skip","건너뛰기 ✕");skip.type="button";
      root.append(prog,skip);
      const mus=opts.music||(opts.music===false?null:DEFAULT_MUSIC);let snd=null,sndBtn=null;const tStart=performance.now();
      if(mus&&mus.src){snd=makeSound(mus);sndBtn=h("button","fx-snd off",'<span class="eq"><i></i><i></i><i></i></span><span class="lb">사운드 켜기</span>');sndBtn.type="button";sndBtn.setAttribute("aria-pressed","false");root.append(sndBtn);
        if(mus.credit)root.append(h("div","fx-mcredit","MUSIC · "+esc(mus.credit)));
        const ui=v=>{sndBtn.classList.toggle("off",!v);sndBtn.querySelector(".lb").textContent=v?"사운드 끄기":"사운드 켜기";sndBtn.setAttribute("aria-pressed",String(v));};
        sndBtn.onclick=()=>{if(snd.on){snd.pause();soundPref.set(false);ui(false);}else{soundPref.set(true);snd.play((performance.now()-tStart)/1000).then(ok=>ui(ok));}};
        if(soundPref.get())snd.play(0).then(ok=>ui(ok));}
      const els=scenes.map((s,i)=>{
        const sc=h("div","fx-scene"+(i%2?" alt":"")+(s.center?" dark":"")+(s.color_on?" color":""));sc.style.setProperty("--d",(s.d||1700)+"ms");
        const img=h("div","fx-img");img.style.background=s.img?`url("${s.img}") center/cover, ${s.color||"#111"}`:(s.color||"#111");
        sc.append(img,h("div","fx-shade"));
        if(s.speed){const sp=h("div","fx-speed");for(let k=0;k<9;k++){const l=h("i");l.style.top=(8+Math.random()*84)+"%";l.style.width=(18+Math.random()*30)+"vw";l.style.animationDelay=(-Math.random()*.7)+"s";l.style.animationDuration=(.45+Math.random()*.5)+"s";sp.append(l);}sc.append(sp);}
        sc.append(h("div","fx-flash"));
        const t=h("div","fx-txt"+(s.center?" center":""));
        if(s.tag)t.append(h("span","fx-tag",esc(s.tag)));
        if(s.big)t.append(h("p","fx-big",s.big));
        if(s.mid)t.append(h("p","fx-mid",s.mid));
        if(s.small)t.append(h("p","fx-small",esc(s.small)));
        sc.append(t);
        if(s.corner){const c=h("div","fx-corner");c.append(h("span",null,esc(s.corner[0]||"")),h("span",null,esc(s.corner[1]||"")));sc.append(c);}
        if(s.credit)sc.append(h("div","fx-credit","PHOTO · "+esc(s.credit)));
        root.append(sc);return sc;});
      root.append(h("div","fx-grain"));
      document.body.append(root);document.body.style.overflow="hidden";
      const imgDivs=els.map(e=>e.querySelector(".fx-img"));
      const verify=scenes.map((s,i)=>check(s.img).then(ok=>{if(ok||!s.img)return;const alt=nextPool();imgDivs[i].style.background=alt?`url("${alt}") center/cover, ${s.color||"#111"}`:`radial-gradient(120% 90% at 30% 20%, ${CFG.accent}33, transparent 60%), ${s.color||"#151a19"}`;const cr=els[i].querySelector(".fx-credit");if(cr)cr.textContent="PHOTO · Wikimedia Commons";}));
      await Promise.race([Promise.all(verify.slice(0,3)),new Promise(r=>setTimeout(r,2500))]);
      requestAnimationFrame(()=>root.classList.add("on"));
      const total=scenes.reduce((a,s)=>a+(s.d||1700),0);let t0=performance.now(),idx=-1,timer=null,raf=null,done=false;
      function count(el){el.querySelectorAll(".fx-count").forEach(n=>{const to=parseFloat(n.dataset.to),dec=(n.dataset.to.split(".")[1]||"").length,s0=performance.now();
        const fin=()=>{n.textContent=to.toLocaleString("en-US",{minimumFractionDigits:dec,maximumFractionDigits:dec});};
        const step=t=>{const k=Math.min(1,(t-s0)/900);const e=1-Math.pow(1-k,3);n.textContent=(to*e).toLocaleString("en-US",{minimumFractionDigits:dec,maximumFractionDigits:dec});if(k<1&&!done)requestAnimationFrame(step);else fin();};requestAnimationFrame(step);setTimeout(fin,1000);});}
      function show(i){els.forEach((e,j)=>e.classList.toggle("on",j===i));count(els[i]);}
      function next(){idx++;if(idx>=els.length){finish();return;}show(idx);timer=setTimeout(next,scenes[idx].d||1700);}
      function tick(){prog.style.width=Math.min(100,(performance.now()-t0)/total*100)+"%";if(!done)raf=requestAnimationFrame(tick);}
      function finish(){if(done)return;done=true;if(snd)snd.stop();clearTimeout(timer);cancelAnimationFrame(raf);root.classList.add("out");document.body.style.overflow="";
        document.removeEventListener("keydown",key);setTimeout(()=>{root.remove();},650);active=null;resolve();}
      const key=e=>{if(e.key==="Escape")finish();};
      skip.onclick=finish;document.addEventListener("keydown",key);
      active={stop:finish};
      next();tick();skip.focus({preventScroll:true});
    });
  }

  const kmFmt=x=>(Math.round(x*10)/10).toString();
  const maxKm=r=>Math.max(...r.dist.map(d=>d[1])), minKm=r=>Math.min(...r.dist.map(d=>d[1]));
  const gain=r=>Math.max(0,...r.dist.map(d=>d[2]||0));
  const when=r=>/^\d{4}-\d{2}-\d{2}$/.test(r.date)?r.date.replace(/-/g,"."):r.date.split("-")[0]+"."+r.date.split("-")[1];
  const ph=(r,i)=>r.photos&&r.photos.length?r.photos[i%r.photos.length]:null;
  const W=CFG.words;

  function introScenes(races){
    const pick=[...races].filter(r=>r.photos&&r.photos.length).sort((a,b)=>(b.level||0)-(a.level||0));
    const order=["lavaredo10k","poonhill","angkor10k","miut17","jungfrau","tmb","kumano","medoc"];
    const sel=order.map(id=>pick.find(r=>r.id===id)).filter(Boolean).concat(pick).filter((r,i,a)=>a.indexOf(r)===i).slice(0,7);
    const S=[];
    const p0=ph(sel[0],0);
    S.push({img:p0&&p0.src,credit:p0&&p0.by,big:esc(W[0]),corner:[CFG.brand,"001"],d:1300,speed:true});
    sel.slice(1,4).forEach((r,i)=>{const p=ph(r,0);S.push({img:p&&p.src,credit:p&&p.by,big:esc(W[(i+1)%W.length]),small:`${r.title} — ${r.city}`,corner:[r.country,when(r)],d:1250,speed:i===0});});
    sel.slice(4,7).forEach((r,i)=>{const p=ph(r,1)||ph(r,0);S.push({img:p&&p.src,credit:p&&p.by,
      mid:`<span class="fx-count" data-to="${kmFmt(maxKm(r))}">0</span> KM`+(gain(r)?`<br><em style="font-style:normal;color:var(--fx-accent)">↑ <span class="fx-count" data-to="${gain(r)}">0</span> M</em>`:""),
      small:r.title,corner:[r.city,when(r)],d:1150});});
    const pl=ph(sel[1]||sel[0],1)||p0;
    S.push({img:pl&&pl.src,credit:pl&&pl.by,center:true,tag:`${races.length} courses · 3—10 people`,big:CFG.brandHtml||esc(CFG.brand),small:CFG.tagline,d:2300});
    return S;
  }
  function courseScenes(r){
    const p=i=>ph(r,i);const S=[];
    S.push({img:p(0)&&p(0).src,credit:p(0)&&p(0).by,tag:r.status,big:esc(r.city.split(" (")[0]),small:r.sub,corner:[r.country,when(r)],d:1500,speed:true});
    S.push({img:(p(1)||p(0))&&(p(1)||p(0)).src,credit:(p(1)||p(0))&&(p(1)||p(0)).by,
      mid:(minKm(r)===maxKm(r)?`<span class="fx-count" data-to="${kmFmt(maxKm(r))}">0</span>`:`${kmFmt(minKm(r))}–<span class="fx-count" data-to="${kmFmt(maxKm(r))}">0</span>`)+" KM"+(gain(r)?`<br><em style="font-style:normal;color:var(--fx-accent)">↑ <span class="fx-count" data-to="${gain(r)}">0</span> M</em>`:""),
      small:r.dist.map(d=>d[0]).join(" · "),corner:[r.title,"LV "+r.level+"/5"],d:1600});
    const p2=p(2)||p(0);
    S.push({img:p2&&p2.src,credit:p2&&p2.by,center:true,big:esc(r.title),small:r.line,d:2100});
    return S;
  }

  function seenIntro(){try{return sessionStorage.getItem("fx-intro")==="1";}catch(e){return false;}}
  function markIntro(){try{sessionStorage.setItem("fx-intro","1");}catch(e){}}

  let FILMS=null;
  function loadFilms(){if(FILMS)return Promise.resolve(FILMS);const path=CFG.filmsPath||"films.json";
    return fetch(path+"?t="+Math.floor(Date.now()/3e5),{cache:"no-store"}).then(r=>r.ok?r.json():{films:[]}).catch(()=>({films:[]})).then(d=>{
      FILMS=(d.films||[]).filter(f=>!f.brand||f.brand==="both"||f.brand===CFG.key).sort((a,b)=>b.date.localeCompare(a.date));return FILMS;});}
  function filmScenes(fm){return fm.scenes.map(s=>Object.assign({},s,{big:s.big?esc(s.big).replace(/\*(.+?)\*/g,"<em>$1</em>"):null,mid:s.mid?esc(s.mid):null}));}
  window.RunFX={
    film,introScenes,courseScenes,
    playIntro(races,force){setPool(races);if(!force&&seenIntro())return Promise.resolve();markIntro();
      return loadFilms().then(fs=>fs.length?film(filmScenes(fs[0]),{label:fs[0].title,style:fs[0].style,music:fs[0].music}):film(introScenes(races),{label:CFG.brand+" 소개 영상"}));},
    playFilm(fm){return film(filmScenes(fm),{label:fm.title,style:fm.style,music:fm.music});},
    playDefault(races){setPool(races);return film(introScenes(races),{label:CFG.brand+" 소개 영상"});},
    reel(host,races){setPool(races);loadFilms().then(fs=>{const box=h("div","fx-reel");
      fs.slice(0,4).forEach(fm=>{const b=document.createElement("button");b.type="button";b.innerHTML="▶ "+esc(fm.title)+"<small>"+esc(fm.date.slice(5).replace("-","."))+"</small>";b.onclick=()=>RunFX.playFilm(fm);box.append(b);});
      const d=document.createElement("button");d.type="button";d.innerHTML="▶ RUN · CLIMB · BREATHE<small>기본</small>";d.onclick=()=>RunFX.playDefault(races);box.append(d);
      host.append(box);});},
    playCourse(r){return film(courseScenes(r),{label:r.title+" 코스 영상"});},
    playButton(label,onClick,light){const b=document.createElement("button");b.type="button";b.className="fx-play"+(light?" light":"");b.innerHTML="<b>▶</b>"+esc(label);b.onclick=onClick;return b;},
    poster(el,r,i,strong){const p=ph(r,0);if(!p)return;const bg=h("div","fx-photo");bg.style.backgroundImage=`url("${p.src}")`;bg.setAttribute("aria-hidden","true");
      const tint=h("div","fx-tint");tint.style.background=strong?`linear-gradient(90deg,${r.color}F2 0%,${r.color}B3 40%,${r.color}33 75%,${r.color}11 100%),linear-gradient(0deg,rgba(0,0,0,.35),transparent 50%)`:`linear-gradient(180deg,${r.color}55 0%,${r.color}22 40%,${r.color}EE 100%)`;el.prepend(bg,tint);},
    gallery(r){const g=h("div","fx-gal");(r.photos||[]).forEach(p=>{const f=h("figure");const im=document.createElement("img");im.src=p.src;im.alt=p.cap;im.loading="lazy";
      const c=h("figcaption",null,esc(p.cap)+`<a href="${esc(p.link)}" target="_blank" rel="noopener">사진 · ${esc(p.by)} · Wikimedia Commons</a>`);f.append(im,c);g.append(f);});return g;}
  };
})();
