# 깃허브 서버에서 목소리(edge-tts)·영상/사진 소재를 받아 fetch/out 에 저장 (PC 없이 릴스 제작용)
import json, os, asyncio, urllib.request, pathlib, traceback
OUT = pathlib.Path("fetch/out"); OUT.mkdir(parents=True, exist_ok=True)
jobs = json.load(open("fetch/jobs.json", encoding="utf-8"))
UA = {"User-Agent": "lifejunjun-film/1.0 (probe2928@gmail.com)"}
log = []
KEEP = {f.name for f in OUT.iterdir()}
async def tts(j):
    import edge_tts
    allb = {}
    for i, t in enumerate(j["texts"]):
        f = OUT / f"{j['name']}_{i:02d}.mp3"
        r = (j.get("rates") or [None] * len(j["texts"]))[i] or j.get("rate", "+8%")
        v = j.get("voice", "ko-KR-HyunsuMultilingualNeural")
        try: c = edge_tts.Communicate(t, v, rate=r, boundary="WordBoundary")
        except TypeError: c = edge_tts.Communicate(t, v, rate=r)
        b = []
        with open(f, "wb") as fh:
            async for ch in c.stream():
                if ch["type"] == "audio": fh.write(ch["data"])
                elif ch["type"] == "WordBoundary": b.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
        allb[f"{i:02d}"] = b
    (OUT / f"{j['name']}_words.json").write_text(json.dumps(allb, ensure_ascii=False, indent=0), encoding="utf-8")
    log.append(f"tts {j['name']} {len(j['texts'])}")
for j in jobs:
    try:
        if j["type"] == "tts":
            asyncio.run(tts(j))
        elif j["type"] == "mixkit":
            import re
            html = urllib.request.urlopen(urllib.request.Request("https://mixkit.co/free-stock-video/%s/" % j["q"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "ignore")
            items = []
            for m in re.finditer(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"', html):
                if m.group(2) not in [i[1] for i in items]: items.append((m.group(1), m.group(2)))
            items = items[: j.get("n", 8)]
            (OUT / f"{j['name']}.txt").write_text("\n".join(f"{i} {s}" for s, i in items), encoding="utf-8")
            for slug, vid in items:
                for q in ("720", "1080"):
                    try:
                        with urllib.request.urlopen(urllib.request.Request(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4", headers={"User-Agent": "Mozilla/5.0"}), timeout=180) as r:
                            (OUT / f"{j['name']}_{vid}.mp4").write_bytes(r.read()); break
                    except Exception: pass
            log.append(f"mixkit {j['name']} {len(items)}")
        elif j["type"] == "stats":
            import datetime
            out = {}
            today = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            for site in ("ljj", "yb"):
                for k in range(j.get("days", 3)):
                    d = (today - datetime.timedelta(days=k)).strftime("%Y%m%d")
                    for m in ("pv", "uv", "sns", "apply"):
                        key = f"{site}_{m}_{d}"
                        try:
                            with urllib.request.urlopen(f"https://abacus.jasoncameron.dev/get/lifejunjun-stats/{key}", timeout=20) as r:
                                out[key] = json.loads(r.read()).get("value", 0)
                        except Exception: out[key] = 0
            def _get(key):
                try:
                    with urllib.request.urlopen(f"https://abacus.jasoncameron.dev/get/lifejunjun-stats/{key}", timeout=20) as r:
                        return json.loads(r.read()).get("value", 0)
                except Exception: return 0
            for slug in j.get("trips", ["tainan", "oman", "uzbekistan"]):
                for k in range(j.get("days", 3)):
                    d = (today - datetime.timedelta(days=k)).strftime("%Y%m%d")
                    for m in ("pv", "uv", "apply"):
                        out[f"go_{slug}_{m}_{d}"] = _get(f"go_{slug}_{m}_{d}")
            for tag in j.get("reels", []):  # reel tags used as ?r=<tag> (source ig)
                for pre in ("r_ig-", "ra_ig-"):
                    out[pre + tag] = _get(pre + tag)
            for key in j.get("keys", []):
                out[key] = _get(key)
            (OUT / "stats.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
            log.append("stats ok")
        elif j["type"] == "url":
            req = urllib.request.Request(j["url"], headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                (OUT / j["name"]).write_bytes(r.read())
            log.append(f"url {j['name']} ok")
        elif j["type"] == "commons_search":
            q = urllib.parse.quote(j["q"]) if False else __import__("urllib.parse").parse.quote(j["q"])
            u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6"
                 f"&gsrlimit={j.get('n', 10)}&gsrsearch={q}&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiurlwidth=1600"
                 "&iiextmetadatafilter=Artist|LicenseShortName|ImageDescription")
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                data = json.loads(r.read())
            (OUT / f"{j['name']}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            for pid, p in (data.get("query", {}).get("pages", {}) or {}).items():
                ii = p["imageinfo"][0]
                mime = ii.get("mime", "")
                if "image" in mime and ii.get("thumburl"):
                    with urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=120) as r:
                        (OUT / f"{j['name']}_{pid}.jpg").write_bytes(r.read())
                elif ("video" in mime or "ogg" in mime) and ii.get("size", 0) < 40_000_000:
                    ext = ii["url"].split("?")[0].rsplit(".", 1)[-1]
                    with urllib.request.urlopen(urllib.request.Request(ii["url"], headers=UA), timeout=300) as r:
                        (OUT / f"{j['name']}_{pid}.{ext}").write_bytes(r.read())
            log.append(f"commons {j['name']} ok")
    except Exception as e:
        log.append(f"FAIL {j.get('name')} {e!r}"); traceback.print_exc()
for f in OUT.iterdir():  # GitHub rejects files over 100MB; keep the push small
    if f.stat().st_size > 45_000_000 and f.name not in KEEP:
        log.append(f"drop {f.name} {f.stat().st_size // 1_000_000}MB"); f.unlink()
(OUT / "log.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
