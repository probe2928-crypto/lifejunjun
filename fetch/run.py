# 깃허브 서버에서 목소리(edge-tts)·영상/사진 소재를 받아 fetch/out 에 저장 (PC 없이 릴스 제작용)
import json, os, asyncio, urllib.request, pathlib, traceback
OUT = pathlib.Path("fetch/out"); OUT.mkdir(parents=True, exist_ok=True)
jobs = json.load(open("fetch/jobs.json", encoding="utf-8"))
UA = {"User-Agent": "lifejunjun-film/1.0 (probe2928@gmail.com)"}
log = []
async def tts(j):
    import edge_tts
    for i, t in enumerate(j["texts"]):
        f = OUT / f"{j['name']}_{i:02d}.mp3"
        r = (j.get("rates") or [None] * len(j["texts"]))[i] or j.get("rate", "+8%")
        await edge_tts.Communicate(t, j.get("voice", "ko-KR-HyunsuMultilingualNeural"), rate=r).save(str(f))
    log.append(f"tts {j['name']} {len(j['texts'])}")
for j in jobs:
    try:
        if j["type"] == "tts":
            asyncio.run(tts(j))
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
                elif ("video" in mime or "ogg" in mime) and ii.get("size", 0) < 60_000_000:
                    ext = ii["url"].split("?")[0].rsplit(".", 1)[-1]
                    with urllib.request.urlopen(urllib.request.Request(ii["url"], headers=UA), timeout=300) as r:
                        (OUT / f"{j['name']}_{pid}.{ext}").write_bytes(r.read())
            log.append(f"commons {j['name']} ok")
    except Exception as e:
        log.append(f"FAIL {j.get('name')} {e!r}"); traceback.print_exc()
(OUT / "log.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
