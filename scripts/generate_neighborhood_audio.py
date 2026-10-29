"""Generate the stressed reading sample for AI_4_5 with Yandex SpeechKit."""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks

STRESSED = """Э́то наш райо́н, здесь наш дом. Райо́н краси́вый, зелёный, недалеко́ нахо́дится лес, мы ча́сто гуля́ем вме́сте там. Наш райо́н но́вый, но здесь уже́ есть метро́, э́то о́чень удо́бно.
А э́то на́ша у́лица. Дома́ здесь но́вые, высо́кие. Вот больни́ца но́мер два́дцать три. Здесь рабо́тает Ни́на Петро́вна. Сле́ва двадца́тая шко́ла, где у́чится Та́ня. Она́ лю́бит изуча́ть иностра́нный язы́к, Та́ня уже́ хорошо́ говори́т по-англи́йски и перево́дит англи́йские те́ксты.
Спра́ва нахо́дятся магази́ны и кинотеа́тр. Вот оди́ннадцатый дом, где мы живём, а там дом но́мер двена́дцать, где живу́т мои́ друзья́. Я иногда́ быва́ю там."""

def main():
    load_dotenv(ROOT / '.env')
    key = os.getenv('YANDEX_SPEECHKIT_API_KEY', '').strip()
    if not key: raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
    voice=os.getenv('YANDEX_SPEECHKIT_VOICE','marina'); role=os.getenv('YANDEX_SPEECHKIT_ROLE','friendly'); speed=float(os.getenv('YANDEX_SPEECHKIT_SPEED','.7'))
    import re
    marked=re.sub(r'([А-Яа-яЁё])\u0301',r'+\1',STRESSED)
    chunks=reading_chunks(marked)
    parts=[]
    for i,chunk in enumerate(chunks,1):
        parts.append(synthesize(chunk,key,voice,role,speed)); print(f'Phrase {i}/{len(chunks)}',flush=True)
    target=ROOT/'tasks/lesson4/neighborhood_reading/reference.wav'
    save_audio(target,(b'\0\0'*6615).join(parts))
    validate_audio(target)
if __name__=='__main__': main()
