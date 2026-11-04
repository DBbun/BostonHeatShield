"""Render the facilitator board's voice narration.

Reads board/audio/*.txt (one narration script per tab or step), renders each to a mono MP3 with Kokoro-82M
(local text-to-speech, no online service), and writes board/audio/narration.js so the board can show the words.

Run with the Kokoro environment's Python (needs kokoro, torch, soundfile, numpy, lameenc):
    python scripts/build_board_audio.py            # only scripts that changed
    python scripts/build_board_audio.py --force    # re-render everything
The voice is synthetic (AI-generated). The board says so next to every player.
"""
import json
import sys
from pathlib import Path

import lameenc
import numpy as np
import torch
from kokoro import KPipeline

AUDIO = Path(__file__).resolve().parent.parent / 'board' / 'audio'
VOICE, SPEED, RATE, KBPS = 'af_heart', 1.0, 24000, 64
force = '--force' in sys.argv

# Written form stays in the transcript; the spoken form below is only used for the voice.
PRONOUNCE = {'NOAA': 'Noah', 'NIHHIS': 'N I H H I S', 'DBbun': 'D B bun', 'EMS': 'E M S', 'Kartoun': 'Kartoon'}

device = 'cuda' if torch.cuda.is_available() else 'cpu'
pipeline = None
narration, total = {}, 0.0
for txt in sorted(AUDIO.glob('*.txt')):
    key = txt.stem
    written = txt.read_text(encoding='utf-8').strip()
    narration[key] = written
    mp3 = AUDIO / f'{key}.mp3'
    if mp3.exists() and mp3.stat().st_mtime >= txt.stat().st_mtime and not force:
        continue
    pipeline = pipeline or KPipeline(lang_code='a', device=device)
    paras = [p.strip().replace('\n', ' ') for p in written.split('\n\n') if p.strip()]
    for a, b in PRONOUNCE.items():
        paras = [p.replace(a, b) for p in paras]
    parts, pause = [], np.zeros(int(RATE * 0.6), dtype=np.float32)
    for para in paras:
        for _, _, audio in pipeline(para, voice=VOICE, speed=SPEED):
            parts.append(audio.cpu().numpy() if hasattr(audio, 'cpu') else np.asarray(audio))
        parts.append(pause)
    wave = np.concatenate(parts)
    pcm = (np.clip(wave, -1, 1) * 32767).astype('<i2').tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(KBPS)
    enc.set_in_sample_rate(RATE)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3.write_bytes(enc.encode(pcm) + enc.flush())
    secs = len(wave) / RATE
    total += secs
    print(f'{key}: {secs:.0f} s, {mp3.stat().st_size / 1e6:.2f} MB', flush=True)

(AUDIO / 'narration.js').write_text('window.NARR = ' + json.dumps(narration, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')
print(f'done: {len(narration)} scripts, {total / 60:.1f} min rendered, device={device}, voice={VOICE}')
