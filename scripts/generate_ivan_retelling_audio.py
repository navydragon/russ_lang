"""Create the AI_4_13 SpeechKit reference with a headphone wake-up cue."""
import os
import re
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks

STRESSED = """Ива́н — журнали́ст. Его́ родно́й язы́к — ру́сский, но он хорошо́ зна́ет англи́йский. Ива́н непло́хо говори́т по-англи́йски и чита́ет англи́йские газе́ты и журна́лы. Сейча́с он у́чит кита́йский язы́к и уже́ немно́го понима́ет по-кита́йски. До́ма Ива́н повторя́ет но́вые кита́йские слова́, пи́шет кита́йские иеро́глифы и чита́ет кита́йские стихи́. Ива́н говори́т, что кита́йский язы́к о́чень тру́дный язы́к, но интере́сный. Он говори́т: «Я не то́лько чита́ю кита́йские стихи́, но и слу́шаю кита́йские пе́сни и смотрю́ кита́йские фи́льмы»."""

def main():
    load_dotenv(ROOT / '.env')
    key = os.getenv('YANDEX_SPEECHKIT_API_KEY', '').strip()
    if not key:
        raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
    voice = os.getenv('YANDEX_SPEECHKIT_VOICE', 'marina')
    role = os.getenv('YANDEX_SPEECHKIT_ROLE', 'friendly')
    speed = float(os.getenv('YANDEX_SPEECHKIT_SPEED', '.7'))
    marked = re.sub(r'([А-Яа-яЁё])\u0301', r'+\1', STRESSED)
    chunks = reading_chunks(marked)
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(synthesize(chunk, key, voice, role, speed))
        print(f'Phrase {i}/{len(chunks)}', flush=True)
    target = ROOT / 'tasks/lesson4/ivan_retelling/reference.wav'
    save_audio(target, (b'\0\0' * 6615).join(parts))
    validate_audio(target)

if __name__ == '__main__':
    main()
