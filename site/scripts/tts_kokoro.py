"""Synthesize narration sections with Kokoro. Called by scripts/audio.ts with a job file; not meant to be run by hand."""
import json
import sys
import time

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro


def trim(audio, sr, floor=0.004, pad=0.03):
    """Cut leading and trailing near-silence so the gaps between sentences are the ones we ask for."""
    loud = np.flatnonzero(np.abs(audio) > floor)
    if loud.size == 0:
        return audio
    keep = int(sr * pad)
    return audio[max(0, loud[0] - keep): loud[-1] + keep]


job = json.load(open(sys.argv[1]))
kokoro = Kokoro(job["model"], job["voices"])
results, started = {}, time.time()
for n, section in enumerate(job["sections"], 1):
    chunks, starts, pos, sr = [], [], 0, 24000
    for item in section["items"]:
        audio, sr = kokoro.create(item["text"], voice=job["voice"], speed=job["speed"], lang=job["lang"])
        audio = trim(np.asarray(audio, dtype=np.float32), sr)
        gap = np.zeros(int(sr * item["gap"]), dtype=np.float32)
        starts.append(round(pos / sr, 3))
        chunks += [audio, gap]
        pos += len(audio) + len(gap)
    data = np.concatenate(chunks)
    sf.write(section["wav"], data, sr, subtype="PCM_16")
    results[section["key"]] = {"duration": round(len(data) / sr, 3), "starts": starts}
    print(f"  [{n}/{len(job['sections'])}] {section['key']}  {len(data) / sr:.0f}s of audio", flush=True)
json.dump(results, open(job["result"], "w"))
print(f"  synthesized in {time.time() - started:.0f}s", flush=True)
