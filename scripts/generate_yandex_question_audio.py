"""Generate the 12 AI_4_3 questions using the course SpeechKit settings."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil

from dotenv import load_dotenv

if __package__:
    from .generate_yandex_dictation_audio import ROOT, mark_stress, synthesize, save_audio, validate_audio
else:
    from generate_yandex_dictation_audio import ROOT, mark_stress, synthesize, save_audio, validate_audio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=('university_questions', 'library_questions'), default='university_questions')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env', override=False)
    key = os.getenv('YANDEX_SPEECHKIT_API_KEY', '').strip()
    if not key:
        raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
    voice = os.getenv('YANDEX_SPEECHKIT_VOICE', 'marina')
    role = os.getenv('YANDEX_SPEECHKIT_ROLE', 'friendly')
    speed = float(os.getenv('YANDEX_SPEECHKIT_SPEED', '.7'))
    directory = ROOT / 'tasks/lesson4' / args.task / 'audio'
    questions = json.loads((directory / 'questions.json').read_text(encoding='utf-8'))
    ready = []
    for question in questions:
        text = mark_stress(question['text'], question['pronunciation'])
        signature = hashlib.sha256(json.dumps([text, voice, role, speed, 'cue150-pause500']).encode()).hexdigest()
        cached = ROOT / '.speechkit-cache/questions' / f'{signature}.wav'
        if not cached.exists():
            save_audio(cached, synthesize(text, key, voice, role, speed))
        validate_audio(cached)
        ready.append((cached, directory / f"{question['id']:02d}.wav"))
        print(f"Question {question['id']}/{len(questions)} ready", flush=True)
    for cached, target in ready:
        temporary = target.with_suffix('.publish.tmp')
        shutil.copyfile(cached, temporary)
        temporary.replace(target)
    print(f'Published {len(questions)} question recordings')


if __name__ == '__main__':
    main()
