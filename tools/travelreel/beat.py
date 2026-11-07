"""Upbeat travel-reel beat (house/pop) synth. usage: beat.py seconds out.wav bpm seed [key]"""
import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
sr = 48000
L = float(sys.argv[1]); out = sys.argv[2]; bpm = float(sys.argv[3]); seed = int(sys.argv[4])
root = int(sys.argv[5]) if len(sys.argv) > 5 else 45  # A2
rng = np.random.default_rng(seed)
N = int((L + 1) * sr); spb = 60 / bpm
mL = np.zeros(N); mR = np.zeros(N); side = np.ones(N)
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def put(sig, t, pan=0.0, g=1.0):
    i = int(t * sr)
    if i >= N: return
    s = sig[:N - i] * g
    mL[i:i + len(s)] += s * (1 - pan); mR[i:i + len(s)] += s * (1 + pan)
def lp(x, f):
    b, a = butter(2, min(0.99, f / (sr / 2))); return lfilter(b, a, x)
def hp(x, f):
    b, a = butter(2, f / (sr / 2), 'high'); return lfilter(b, a, x)
# drums
tk = np.arange(int(0.35 * sr)) / sr
kick = np.sin(2 * np.pi * (45 * tk + 90 * (1 - np.exp(-tk * 35)) / 35 * 1)) * np.exp(-tk * 7.5)
kick += 0.4 * np.sin(2 * np.pi * 55 * tk) * np.exp(-tk * 10)
nz = rng.standard_normal(int(0.25 * sr))
clap = hp(nz, 900) * np.exp(-np.arange(len(nz)) / sr * 18)
for d in (0.008, 0.017):
    k = int(d * sr); clap[k:] += 0.6 * clap[:-k]
hat = hp(rng.standard_normal(int(0.06 * sr)), 7000) * np.exp(-np.arange(int(0.06 * sr)) / sr * 70)
ohat = hp(rng.standard_normal(int(0.2 * sr)), 6000) * np.exp(-np.arange(int(0.2 * sr)) / sr * 18)
# progression: i - VI - III - VII (minor, uplifting)
prog = [[0, 3, 7, 10], [-4, 0, 3, 7], [3, 7, 10, 14], [-2, 2, 5, 9]]
bars = int(L / (4 * spb)) + 2
for b in range(bars):
    t0 = b * 4 * spb
    ch = prog[(b // 1) % 4]
    intro = b < 1
    for q in range(4):
        tb = t0 + q * spb
        if not intro:
            put(kick, tb, g=0.95)
            ii = int(tb * sr); n = int(0.22 * sr)
            if ii < N: side[ii:ii + n] = np.minimum(side[ii:ii + n], 0.35 + 0.65 * (np.arange(min(n, N - ii)) / n))
        if q in (1, 3) and not intro: put(clap, tb, g=0.33)
        put(hat, tb + spb / 2, pan=0.3, g=0.22 if not intro else 0.12)
        if b % 2 == 1 and q == 3: put(ohat, tb + spb * 0.75, pan=-0.3, g=0.15)
        for s16 in (0.25, 0.75):
            put(hat, tb + spb * s16, pan=-0.2, g=0.07)
        # offbeat bass
        tbb = np.arange(int(spb * 0.45 * sr)) / sr
        f0 = hz(root + ch[0] - 12)
        bs = (np.sin(2 * np.pi * f0 * tbb) + 0.3 * np.sign(np.sin(2 * np.pi * f0 * tbb))) * np.minimum(1, tbb / 0.01) * np.exp(-tbb * 4)
        if not intro: put(lp(bs, 900), tb + spb / 2, g=0.22)
        # chord stab on offbeats (pluck)
        tp = np.arange(int(0.35 * sr)) / sr
        st = sum(np.sin(2 * np.pi * hz(root + 12 + n) * tp + rng.random()) + 0.5 * np.sin(4 * np.pi * hz(root + 12 + n) * tp)
                 for n in ch) * np.exp(-tp * 9) * np.minimum(1, tp / 0.003)
        put(lp(st, 3500), tb + spb / 2, pan=0.15 * (-1) ** q, g=0.05)
    # pad (sidechained later)
    tpd = np.arange(int(4 * spb * sr)) / sr
    pad = sum(np.sin(2 * np.pi * hz(root + 12 + n) * tpd * (1 + dd)) for n in ch for dd in (-0.003, 0.003))
    pad = lp(pad, 1800 if not intro else 700) * np.minimum(1, tpd / 0.3)
    put(pad * 0.028, t0, pan=0.0)
    # lead hook every other bar
    if b >= 2 and b % 2 == 0:
        mel = [ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        for i, n in enumerate(mel):
            tm = np.arange(int(spb * 0.6 * sr)) / sr
            f0 = hz(root + 12 + n)
            ld = (np.sin(2 * np.pi * f0 * tm) + 0.25 * np.sin(6 * np.pi * f0 * tm)) * np.exp(-tm * 5) * np.minimum(1, tm / 0.005)
            put(ld, t0 + i * spb * 0.5 + spb * 0.5, pan=0.2, g=0.06)
# sidechain the whole non-kick bed lightly
mL *= (0.55 + 0.45 * side); mR *= (0.55 + 0.45 * side)
ir_n = int(1.2 * sr); ti = np.arange(ir_n) / sr
ir = rng.standard_normal(ir_n) * np.exp(-ti * 4); ir = lp(ir, 4000); ir /= np.abs(ir).sum() ** 0.5 * 6
mL = mL + 0.18 * fftconvolve(mL, ir)[:N]; mR = mR + 0.18 * fftconvolve(mR, ir[::-1])[:N]
x = np.stack([mL, mR], 1)[: int(L * sr)]
x = np.tanh(x / np.abs(x).max() * 1.6) ; x /= np.abs(x).max() / 0.85
wavfile.write(out, sr, (x * 32767).astype(np.int16))
print('ok', L, bpm)
