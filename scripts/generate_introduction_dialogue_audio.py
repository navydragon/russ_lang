"""Create a Yandex SpeechKit reading sample for AI_4_9."""
import os, re
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks
STRESSED = """Здра́вствуйте, Серге́й Ива́нович! Здра́вствуйте! Серге́й Ива́нович, познако́мьтесь, пожа́луйста. Э́то мой друг Джон. Джон, э́то мой ру́сский преподава́тель, Серге́й Ива́нович. О́чень прия́тно! О́чень прия́тно! Джон, вы студе́нт? Нет, я уже́ рабо́таю. Я инжене́р. Друзья́, вы лю́бите ко́фе? Да, коне́чно. Вот, пожа́луйста. Большо́е спаси́бо."""
def main():
 load_dotenv(ROOT/'.env'); key=os.getenv('YANDEX_SPEECHKIT_API_KEY','').strip()
 if not key: raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
 voice=os.getenv('YANDEX_SPEECHKIT_VOICE','marina'); role=os.getenv('YANDEX_SPEECHKIT_ROLE','friendly'); speed=float(os.getenv('YANDEX_SPEECHKIT_SPEED','.7'))
 marked=re.sub(r'([А-Яа-яЁё])\u0301',r'+\1',STRESSED); chunks=reading_chunks(marked);parts=[]
 for i,chunk in enumerate(chunks,1):
  parts.append(synthesize(chunk,key,voice,role,speed));print(f'Phrase {i}/{len(chunks)}',flush=True)
 target=ROOT/'tasks/lesson4/introduction_dialogue/reference.wav';save_audio(target,(b'\0\0'*6615).join(parts));validate_audio(target)
if __name__=='__main__': main()
