"""Prepare and optionally publish both lesson-four reading samples via SpeechKit."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import uuid

from dotenv import load_dotenv

if __package__:
    from .generate_yandex_dictation_audio import ROOT, mark_stress, save_audio, synthesize, validate_audio
else:
    from generate_yandex_dictation_audio import ROOT, mark_stress, save_audio, synthesize, validate_audio


def reading_chunks(text, limit=180):
    """Stay within standard SpeechKit limits, prefer complete sentences."""
    chunks, buffer = [], ''
    for word in text.split():
        if len(word) > limit:
            raise ValueError('A reading token exceeds the standard request size')
        candidate = (buffer + ' ' + word).strip()
        if len(candidate) > limit:
            chunks.append(buffer)
            buffer = word
        else:
            buffer = candidate
        if re.search(r'[.!?][»”]?$', word):
            chunks.append(buffer)
            buffer = ''
    if buffer:
        chunks.append(buffer)
    return chunks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env', override=False)
    key = os.getenv('YANDEX_SPEECHKIT_API_KEY', '').strip()
    if not key:
        parser.error('Set YANDEX_SPEECHKIT_API_KEY in .env')
    voice = os.getenv('YANDEX_SPEECHKIT_VOICE', 'marina')
    role = os.getenv('YANDEX_SPEECHKIT_ROLE', 'friendly')
    speed = float(os.getenv('YANDEX_SPEECHKIT_SPEED', '.7'))
    task = ROOT / 'tasks/lesson4/university_reading'
    bank = json.loads((task / 'yandex-reading.json').read_text(encoding='utf-8'))
    outputs = []
    for part in bank['parts']:
        if part['stressed_text'].replace('\u0301', '') != part['text']:
            raise ValueError('Accented text must preserve the reference exactly')
        text = mark_stress(part['text'], part['pronunciation'])
        digest = hashlib.sha256(json.dumps([text, voice, role, speed, 'cue150-pause500']).encode()).hexdigest()
        cached = ROOT / '.speechkit-cache/reading' / f'{digest}.wav'
        if not cached.exists():
            fragments = []
            chunks = reading_chunks(text)
            for index, chunk in enumerate(chunks, 1):
                signature = hashlib.sha256(json.dumps([chunk, voice, role, speed]).encode()).hexdigest()
                piece = ROOT / '.speechkit-cache/reading-chunks' / f'{signature}.pcm'
                if not piece.exists():
                    pcm = synthesize(chunk, key, voice, role, speed)
                    piece.parent.mkdir(parents=True, exist_ok=True)
                    piece.write_bytes(pcm)
                fragments.append(piece.read_bytes())
                print(f"Part {part['id']}: phrase {index}/{len(chunks)} ready", flush=True)
            # One cue for the whole part; short natural gaps separate phrases.
            save_audio(cached, (b'\0\0' * 6615).join(fragments))
        validate_audio(cached)
        directory = task if part['id'] == 1 else ROOT / 'tasks/lesson4/university_reading_part2'
        outputs.append((cached, directory / 'reference.wav'))
        print(f"Part {part['id']} ready: {voice} / {role} / {speed}", flush=True)
    if not args.publish:
        print('Samples cached; use --publish to replace lesson audio')
        return
    backup = ROOT / '.speechkit-cache/backups' / uuid.uuid4().hex
    originals = []
    for _, target in outputs:
        if target.exists():
            old = backup / target.relative_to(ROOT)
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target, old)
            originals.append((old, target))
    try:
        for cached, target in outputs:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix('.publish.tmp')
            shutil.copyfile(cached, temporary)
            temporary.replace(target)
    except OSError:
        for old, target in originals:
            shutil.copyfile(old, target)
        raise
    print('Published both separate reading samples; source MP3 files are preserved')


if __name__ == '__main__':
    main()
