"""Generate SpeechKit samples or stage and publish all four dictations."""
import argparse
import base64
import json
import hashlib
import shutil
import uuid
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import wave

from dotenv import load_dotenv

if __package__:
    from .add_dictation_cue import add_cue
else:
    from add_dictation_cue import add_cue

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis'
SAMPLE_RATE = 22050


def mark_stress(text, pronunciation):
    """Preserve punctuation; translate written acute accents into SpeechKit +vowel."""
    lexicon = {part['text'].casefold(): part['stressed'] for part in pronunciation}

    def replace(match):
        word = match.group()
        if word.casefold() == 'и' and word.casefold() not in lexicon:
            return word
        stressed = lexicon[word.casefold()]
        if '\u0301' not in stressed:
            return word  # Monosyllables and ё already have unambiguous stress.
        index = stressed.index('\u0301') - 1
        return word[:index] + '+' + word[index:]

    return re.sub(r'\w+', replace, text)


def decode_audio(response):
    chunks = []
    for line in response:
        if not line.strip():
            continue
        message = json.loads(line)
        if 'error' in message:
            raise ValueError('SpeechKit returned a synthesis error')
        result = message.get('result', message)
        encoded = result.get('audioChunk', {}).get('data')
        if encoded:
            chunks.append(base64.b64decode(encoded, validate=True))
    audio = b''.join(chunks)
    if not audio or len(audio) % 2:
        raise ValueError('SpeechKit returned empty or invalid PCM audio')
    return audio


def save_audio(path, pcm):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.speechkit-', dir=path.parent) as directory:
        temporary = Path(directory) / 'sample.wav'
        with wave.open(str(temporary), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(b'\0\0' * round(SAMPLE_RATE * .5) + pcm)
        add_cue(temporary)
        temporary.replace(path)


TASK_DIRECTORIES = ('dictation_1', 'dictation_2', 'dictation_3', 'novgorod_dictation')


def task_items(directory):
    task = ROOT / 'tasks/lesson3' / directory
    bank = json.loads((task / 'audio/words.json').read_text(encoding='utf-8'))
    if directory == 'novgorod_dictation':
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from api.dictation import NOVGOROD_SENTENCES
        texts = NOVGOROD_SENTENCES
    else:
        texts = [item['noun'] for item in bank]
    return [(item['id'], mark_stress(text, item['pronunciation'])) for item, text in zip(bank, texts)]


def synthesize(text, key, voice, role, speed):
    payload = {
        'text': text,
        'hints': [{'voice': voice}, {'role': role}, {'speed': speed}],
        'outputAudioSpec': {'rawAudio': {'audioEncoding': 'LINEAR16_PCM', 'sampleRateHertz': SAMPLE_RATE}},
        'loudnessNormalizationType': 'LUFS',
    }
    request = Request(ENDPOINT, json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                      headers={'Authorization': 'Api-Key ' + key, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=60) as response:
            return decode_audio(response)
    except HTTPError as error:
        raise SystemExit(f'SpeechKit HTTP {error.code}; published lesson files were not changed') from None
    except URLError as error:
        raise SystemExit(f'SpeechKit network failure ({type(error.reason).__name__}); published lesson files were not changed') from None
    except (ValueError, TimeoutError) as error:
        raise SystemExit(f'SpeechKit request failed ({type(error).__name__}); published lesson files were not changed') from None


def validate_audio(path):
    with wave.open(str(path)) as sound:
        if sound.getnchannels() != 1 or sound.getsampwidth() != 2 or sound.getframerate() != SAMPLE_RATE:
            raise ValueError(f'Invalid WAV format: {path.name}')
        if sound.getnframes() <= round(SAMPLE_RATE * .65):
            raise ValueError(f'Empty speech: {path.name}')


def generate_all(key, voice, role, speed, publish, directories=None):
    directories = TASK_DIRECTORIES if directories is None else directories
    total = sum(len(task_items(directory)) for directory in directories)
    prepared = []
    for directory in directories:
        for word_id, text in task_items(directory):
            settings = {'text': text, 'voice': voice, 'role': role, 'speed': speed, 'prefix': 'cue150-pause500-v1'}
            digest = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
            cached = ROOT / '.speechkit-cache' / 'generated' / directory / (digest + '.wav')
            if not cached.exists():
                save_audio(cached, synthesize(text, key, voice, role, speed))
                status = 'Generated'
            else:
                status = 'Reused'
            validate_audio(cached)
            target = ROOT / 'tasks/lesson3' / directory / 'audio' / f'{word_id:02d}.wav'
            prepared.append((cached, target))
            print(f'{status}: {directory}/{word_id:02d} ({len(prepared)}/{total})', flush=True)
    if not publish:
        print('All files staged. Add --publish to replace lesson audio without repeating successful requests.')
        return
    # Every network request and WAV validation succeeds before replacing any published file.
    backup = ROOT / '.speechkit-cache' / 'backups' / uuid.uuid4().hex
    originals = []
    for _, target in prepared:
        original = backup / target.relative_to(ROOT)
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, original)
        originals.append((original, target))
    try:
        for cached, target in prepared:
            replacement = target.with_suffix('.publish.tmp')
            shutil.copyfile(cached, replacement)
            replacement.replace(target)
    except OSError:
        for original, target in originals:
            shutil.copyfile(original, target)
        raise
    print(f'Published {len(prepared)} recordings. Previous WAV files backed up in {backup}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--sentence', type=int, choices=range(1, 11))
    selection.add_argument('--all', action='store_true', help='Generate all four dictations')
    selection.add_argument('--task', choices=TASK_DIRECTORIES, help='Generate just one dictation')
    parser.add_argument('--publish', action='store_true', help='Replace lesson audio after all files are ready')
    args = parser.parse_args()
    if args.publish and not (args.all or args.task):
        parser.error('--publish requires --all or --task')
    load_dotenv(ROOT / '.env', override=False)
    key = os.getenv('YANDEX_SPEECHKIT_API_KEY', '').strip()
    if not key:
        parser.error('Set YANDEX_SPEECHKIT_API_KEY in .env')
    voice = os.getenv('YANDEX_SPEECHKIT_VOICE', 'marina').strip()
    role = os.getenv('YANDEX_SPEECHKIT_ROLE', 'friendly').strip()
    speed = float(os.getenv('YANDEX_SPEECHKIT_SPEED', '0.7'))
    if not .1 <= speed <= 3:
        parser.error('Speech speed must be between 0.1 and 3')
    print(f'Voice: {voice}; role: {role}; speed: {speed}', flush=True)
    if args.all or args.task:
        directories = (args.task,) if args.task else None
        generate_all(key, voice, role, speed, args.publish, directories)
    else:
        sentence = args.sentence or 5
        text = task_items('novgorod_dictation')[sentence - 1][1]
        pcm = synthesize(text, key, voice, role, speed)
        target = ROOT / 'tasks/lesson3/novgorod_dictation/samples' / f'yandex_{sentence:02d}.wav'
        save_audio(target, pcm)
        print(f'Text: {text}')
        print(f'Saved sample: {target}')


if __name__ == '__main__':
    main()
