"""Generate four AI_4_7 dialogue recordings."""
import os,re
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks

STRESSED = (
"Вы говори́те по-ру́сски? Да, говорю́. Где гру́ппа но́мер четы́ре? Я не понима́ю, когда́ вы говори́те бы́стро.",
"Ребя́та! Когда́ вы обе́даете? Обы́чно мы обе́даем по́сле уро́ка. Что вы де́лаете пото́м? Гуля́ем. Почему́ ты спра́шиваешь? Потому́ что сего́дня днём футбо́л.",
"Что э́то? Аудито́рия? Нет, э́то декана́т. Где аудито́рия но́мер три? Спра́ва.",
"Ли́лия, ты ещё у́чишь слова́? Нет, я уже́ де́лаю упражне́ние. А я перевожу́ текст. Не зна́ю, что зна́чит э́то сло́во. Ты не зна́ешь? То́же не зна́ю.",
)
def main():
 load_dotenv(ROOT/'.env'); key=os.getenv('YANDEX_SPEECHKIT_API_KEY','').strip()
 if not key: raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
 voice=os.getenv('YANDEX_SPEECHKIT_VOICE','marina');role=os.getenv('YANDEX_SPEECHKIT_ROLE','friendly');speed=float(os.getenv('YANDEX_SPEECHKIT_SPEED','.7'))
 dest=ROOT/'tasks/lesson4/dialogue_reading/audio';dest.mkdir(exist_ok=True)
 for i,text in enumerate(STRESSED,1):
  marked=re.sub(r'([А-Яа-яЁё])\u0301',r'+\1',text); chunks=reading_chunks(marked)
  parts=[synthesize(chunk,key,voice,role,speed) for chunk in chunks]
  target=dest/f'{i}.wav';save_audio(target,(b'\0\0'*6615).join(parts));validate_audio(target);print(f'Dialogue {i}/4 ready',flush=True)
if __name__=='__main__': main()
