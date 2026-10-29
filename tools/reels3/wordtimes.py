# caption word reveal times from edge-tts word boundaries
import re, subprocess, numpy as np
def lead_silence(mp3, thr_db=-45):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    thr = 10 ** (thr_db / 20); idx = np.nonzero(np.abs(a) > thr)[0]
    return idx[0] / 16000 if len(idx) else 0.0
def pieces(text):
    out = []
    for ln in text.split("\n"):
        for w in ln.replace("[", "").replace("]", "").split(" "):
            if w: out.append(w)
    return out
def norm(s): return re.sub(r"[^0-9A-Za-z가-힣]", "", s)
def caption_times(cap, words, t_phrase, lead, tempo, t0):
    """words: [{w,s,e}] for the phrase (raw mp3 seconds). Returns absolute reveal time per caption piece."""
    vt = [(norm(w["w"]), t_phrase + max(0, w["s"] - lead) / tempo) for w in words]
    ps = pieces(cap); res = [None] * len(ps); j = 0
    for i, p in enumerate(ps):
        core = norm(p)[:2]
        if not core: continue
        for k in range(j, len(vt)):
            if core in vt[k][0] or (len(vt[k][0]) >= 2 and vt[k][0][:2] in norm(p)):
                res[i] = vt[k][1]; j = k + 1; break
    res[0] = t0
    # fill gaps by interpolation, keep monotonic
    end = (t_phrase + max(0, words[-1]["e"] - lead) / tempo) if words else t0 + 1
    known = [(i, v) for i, v in enumerate(res) if v is not None]
    for i in range(len(res)):
        if res[i] is None:
            a = max((kv for kv in known if kv[0] < i), key=lambda kv: kv[0])
            b = min((kv for kv in known if kv[0] > i), key=lambda kv: kv[0], default=(len(res), end))
            res[i] = a[1] + (b[1] - a[1]) * (i - a[0]) / (b[0] - a[0])
    for i in range(1, len(res)): res[i] = max(res[i], res[i - 1])
    return [round(x, 3) for x in res]
