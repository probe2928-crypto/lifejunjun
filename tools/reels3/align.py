# 보이스 파일 → 단어별 타임스탬프 (자막 싱크용). PC에서 실행: python align.py voice.mp3 out.json
# 필요: pip install faster-whisper (모델 small 자동 다운로드), ffmpeg
import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(audio, language="ko", word_timestamps=True, vad_filter=False, beam_size=5)
words = []
for s in segs:
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})
json.dump(words, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("words", len(words))
