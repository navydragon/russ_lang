"""Create a Yandex SpeechKit reading sample for AI_4_10."""
import os, re
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks
STRESSED = """Что вы де́лаете в свобо́дное вре́мя? Чита́ем. Слу́шаем му́зыку. Смо́трим фильм. А вы смо́трите ру́сские фи́льмы? Иногда́. Я ду́маю, что вы ча́сто смо́трите спорт. Коне́чно. Осо́бенно футбо́л. Джон, вы непло́хо говори́те по-ру́сски. Вы давно́ изуча́ете ру́сский язы́к? Нет, нет. Что вы! Я пло́хо говорю́, но я рабо́таю. Чита́ю по-ру́сски, слу́шаю, смотрю́ фи́льмы. И всё понима́ете? Коне́чно, нет."""

def main():
 load_dotenv(ROOT/'.env'); key=os.getenv('YANDEX_SPEECHKIT_API_KEY','').strip()
 if not key: raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
 voice=os.getenv('YANDEX_SPEECHKIT_VOICE','marina'); role=os.getenv('YANDEX_SPEECHKIT_ROLE','friendly'); speed=float(os.getenv('YANDEX_SPEECHKIT_SPEED','.7'))
 marked=re.sub(r'([А-Яа-яЁё])\u0301',r'+\1',STRESSED); chunks=reading_chunks(marked);parts=[]
 for i,chunk in enumerate(chunks,1):
  parts.append(synthesize(chunk,key,voice,role,speed));print(f'Phrase {i}/{len(chunks)}',flush=True)
 target=ROOT/'tasks/lesson4/free_time_dialogue/reference.wav';save_audio(target,(b'\0\0'*6615).join(parts));validate_audio(target)
if __name__=='__main__': main()
