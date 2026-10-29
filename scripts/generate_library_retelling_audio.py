"""Create a Yandex SpeechKit reading sample for AI_4_12."""
import os, re, wave
from dotenv import load_dotenv
from generate_yandex_dictation_audio import ROOT, synthesize, save_audio, validate_audio
from generate_yandex_reading_audio import reading_chunks
STRESSED = """Э́то библиоте́ка. У́тром, днём и ве́чером тут рабо́тают студе́нты. Они́ чита́ют кни́ги и газе́ты, де́лают упражне́ния, пи́шут пи́сьма. Сего́дня здесь то́же рабо́тают студе́нты. Вот Али́, Ли́лия и Анто́н. Ли́лия де́лает упражне́ние, Али́ чита́ет текст, а Анто́н перево́дит статью́. Иногда́ Ли́лия и Али́ негро́мко разгова́ривают. Когда́ Ли́лия не понима́ет сло́во, она́ спра́шивает Али́: «Что зна́чит э́то сло́во?» Али́ объясня́ет. Сейча́с Ли́лия зна́ет э́то сло́во. Пото́м они́ вме́сте у́чат слова́. Они́ спра́шивают друг дру́га. Снача́ла Али́ спра́шивает, что зна́чит сло́во — столо́вая. Ли́лия отвеча́ет бы́стро и пра́вильно. Пото́м Ли́лия спра́шивает, что зна́чат слова́: чита́ть, писа́ть, знать. Али́ отвеча́ет пра́вильно. Ли́лия говори́т, что она́ хорошо́ зна́ет слова́. Пото́м она́ пи́шет письмо́. Ли́лия пи́шет, что сейча́с она́ изуча́ет ру́сский язы́к. Когда́ Ли́лия пи́шет письмо́, Али́ чита́ет журна́л «Нау́ка и жизнь». Ве́чером они́ вме́сте гуля́ют и у́жинают."""

def add_extra_start_pause(target):
 with wave.open(str(target), 'rb') as audio:
  params = audio.getparams(); frames = audio.readframes(params.nframes)
 cue = round(params.framerate * .15) * params.sampwidth * params.nchannels
 silence = b'\0' * (round(params.framerate * .5) * params.sampwidth * params.nchannels)
 temporary = target.with_suffix('.pause.tmp')
 with wave.open(str(temporary), 'wb') as audio:
  audio.setparams(params); audio.writeframes(frames[:cue] + silence + frames[cue:])
 temporary.replace(target)

def main():
 load_dotenv(ROOT/'.env'); key=os.getenv('YANDEX_SPEECHKIT_API_KEY','').strip()
 if not key: raise SystemExit('Set YANDEX_SPEECHKIT_API_KEY in .env')
 voice=os.getenv('YANDEX_SPEECHKIT_VOICE','marina'); role=os.getenv('YANDEX_SPEECHKIT_ROLE','friendly'); speed=float(os.getenv('YANDEX_SPEECHKIT_SPEED','.7'))
 marked=re.sub(r'([А-Яа-яЁё])\u0301',r'+\1',STRESSED); chunks=reading_chunks(marked);parts=[]
 for i,chunk in enumerate(chunks,1):
  parts.append(synthesize(chunk,key,voice,role,speed));print(f'Phrase {i}/{len(chunks)}',flush=True)
 target=ROOT/'tasks/lesson4/library_retelling/reference.wav';save_audio(target,(b'\0\0'*6615).join(parts));add_extra_start_pause(target);validate_audio(target)
if __name__=='__main__': main()
