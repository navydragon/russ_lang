from io import StringIO
from pathlib import Path
import wave

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from api.dictation import WORDS, choose_words, grade_answer
from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE


class DictationGradingTests(SimpleTestCase):
    def test_ten_unique_words_are_selected_from_the_twenty_five(self):
        selected = choose_words()
        self.assertEqual(len(selected), 10)
        self.assertEqual(len(set(selected)), 10)
        self.assertTrue(set(selected) <= set(range(1, 26)))

    def test_five_points_for_each_independent_component(self):
        for text, noun, pronoun in [
            ('мой класс', 5, 5), ('МОЙ КЛАСС.', 5, 5), ('моя класс', 5, 0),
            ('мой класт', 0, 5), ('моя класт', 0, 0), ('класс', 5, 0),
            ('мой', 0, 5), ('', 0, 0), ('мой моя класс', 0, 0),
        ]:
            with self.subTest(text=text):
                result = grade_answer(1, text)
                self.assertEqual((result['noun_points'], result['pronoun_points']), (noun, pronoun))
                self.assertEqual(result['score'], noun + pronoun)

    def test_all_expected_answers_are_worth_ten(self):
        for word in WORDS:
            self.assertEqual(grade_answer(word['id'], word['answer'])['score'], 10)

    def test_all_twenty_five_audio_files_are_nonempty_russian_voice_assets(self):
        for word in WORDS:
            path = Path(settings.BASE_DIR) / f"tasks/lesson3/dictation_1/audio/{word['id']:02d}.wav"
            with wave.open(str(path)) as sound:
                duration = sound.getnframes() / sound.getframerate()
                self.assertGreater(duration, 0.2)
                self.assertLess(duration, 10)


@override_settings(DEBUG=True)
class DictationAPITests(TestCase):
    def setUp(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def start(self):
        response = self.client.post('/api/dictation/start', {
            'task_code': 'AI_3_7', 'student_code': TEST_STUDENT_CODE,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def answer(self, run_id, index, text, **extra):
        return self.client.post('/api/dictation/answer', {
            'run_id': run_id, 'index': index, 'answer': text, **extra,
        }, content_type='application/json')

    def test_start_does_not_expose_future_words_or_answers(self):
        state = self.start()
        self.assertNotIn('words', state)
        self.assertNotIn('expected', state['current'])
        self.assertEqual(state['answers'], [])
        response = self.client.get('/api/dictation/state', {'run_id': state['run_id']})
        self.assertEqual(response.json()['current'], state['current'])
        audio = self.client.get(state['current']['audio_path'])
        self.assertEqual(audio.status_code, 200)
        audio.close()

    def test_answers_cannot_be_reordered_or_changed(self):
        run = self.start()
        self.assertEqual(self.answer(run['run_id'], 2, 'мой класс').status_code, 409)
        response = self.answer(run['run_id'], 0, 'мой класт', score=100)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.json()['score'], 10)
        repeated = self.answer(run['run_id'], 0, 'мой класт')
        self.assertEqual(repeated.json()['answered'], 1)
        self.assertEqual(self.answer(run['run_id'], 0, 'другой ответ').status_code, 409)

    def test_sixty_passes_and_last_answer_retries_do_not_duplicate_results(self):
        run = self.start()
        private = Session.objects.get(pk=run['run_id']).get_decoded()['ai_dictation']
        for index, word_id in enumerate(private['words']):
            text = WORDS[word_id - 1]['answer'] if index < 6 else ''
            response = self.answer(run['run_id'], index, text)
            self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state['score'], 60)
        self.assertTrue(state['ok'])
        self.assertTrue(state['saved'])
        self.answer(run['run_id'], 9, '')
        self.assertEqual(TaskAttempt.objects.filter(task__code='AI_3_7').count(), 1)
        attempt = TaskAttempt.objects.get()
        self.assertEqual(attempt.student.code, TEST_STUDENT_CODE)
        self.assertEqual(attempt.score, 60)
        self.assertTrue(attempt.is_completed)

    def test_fifty_five_fails_and_wrong_attempt_is_also_saved(self):
        run = self.start()
        private = Session.objects.get(pk=run['run_id']).get_decoded()['ai_dictation']
        for index, word_id in enumerate(private['words']):
            word = WORDS[word_id - 1]
            text = word['answer'] if index < 5 else word['noun'] if index == 5 else ''
            response = self.answer(run['run_id'], index, text)
        self.assertEqual(response.json()['score'], 55)
        self.assertFalse(response.json()['ok'])
        self.assertTrue(response.json()['saved'])
        self.assertFalse(TaskAttempt.objects.get().is_completed)

    def test_missing_run_and_invalid_input_are_rejected(self):
        self.assertEqual(self.client.get('/api/dictation/state', {'run_id': 'bad'}).status_code, 404)
        run = self.start()
        self.assertEqual(self.answer(run['run_id'], 0, 'а' * 201).status_code, 400)


class PluralDictationGradingTests(SimpleTestCase):
    def test_five_unique_pairs(self):
        from api.dictation import choose_words
        selected = choose_words('AI_3_8')
        self.assertEqual(len(selected), 5)
        self.assertEqual(len(set(selected)), 5)
        self.assertTrue(set(selected) <= set(range(1, 18)))

    def test_independent_ten_points_and_normalization(self):
        for text, points in [('лампы и карандаши', 20), ('ЛАМПЫ, КАРАНДАШИ!', 20),
                             ('лампа и карандаши', 10), ('лампы и карандаш', 10),
                             ('лампы', 10), ('карандаши', 10), ('', 0),
                             ('лампы карандаши газеты', 0)]:
            with self.subTest(text=text):
                self.assertEqual(grade_answer(1, text, 'AI_3_8')['score'], points)
        self.assertEqual(grade_answer(16, 'сестры и товарищи', 'AI_3_8')['score'], 20)

    def test_every_pair_and_audio_asset(self):
        from api.dictation import PAIR_ANSWERS
        for i, text in enumerate(PAIR_ANSWERS, 1):
            self.assertEqual(grade_answer(i, text, 'AI_3_8')['score'], 20)
            with wave.open(str(Path(settings.BASE_DIR) / f'tasks/lesson3/dictation_2/audio/{i:02d}.wav')) as sound:
                self.assertGreater(sound.getnframes() / sound.getframerate(), 0.2)


@override_settings(DEBUG=True)
class PluralDictationAPITests(TestCase):
    def setUp(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_thresholds_persistence_and_retry(self):
        from api.dictation import PAIR_ANSWERS
        for target in (60, 50):
            response = self.client.post('/api/dictation/start', {
                'task_code': 'AI_3_8', 'student_code': TEST_STUDENT_CODE,
            }, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            run = response.json()
            self.assertEqual(run['word_count'], 5)
            self.assertEqual(run['item_max_score'], 20)
            self.assertNotIn('words', run)
            self.assertNotIn('expected', run['current'])
            audio = self.client.get(run['current']['audio_path'])
            self.assertEqual(audio.status_code, 200)
            audio.close()
            words = Session.objects.get(pk=run['run_id']).get_decoded()['ai_dictation']['words']
            for index, word_id in enumerate(words):
                expected = PAIR_ANSWERS[word_id - 1]
                text = expected if index < 2 else (expected if target == 60 else expected.split(' и ')[0]) if index == 2 else ''
                response = self.client.post('/api/dictation/answer', {
                    'run_id': run['run_id'], 'index': index, 'answer': text, 'score': 100,
                }, content_type='application/json')
                self.assertEqual(response.status_code, 200)
            final = response.json()
            self.assertTrue(final['completed'])
            self.assertTrue(final['saved'])
            self.assertEqual(final['score'], target)
            self.assertEqual(final['ok'], target >= 60)
            self.client.post('/api/dictation/answer', {
                'run_id': run['run_id'], 'index': 4, 'answer': '',
            }, content_type='application/json')
        attempts = TaskAttempt.objects.filter(task__code='AI_3_8').order_by('pk')
        self.assertEqual(list(attempts.values_list('score', flat=True)), [60, 50])
        self.assertEqual(list(attempts.values_list('is_completed', flat=True)), [True, False])


class DictationPronunciationTests(SimpleTestCase):
    def test_pronunciation_matches_spoken_text_and_has_explicit_stress(self):
        import json
        vowels = set('аеёиоуыэюя')
        for directory in ('dictation_1', 'dictation_2', 'dictation_3'):
            path = Path(settings.BASE_DIR) / 'tasks/lesson3' / directory / 'audio/words.json'
            for item in json.loads(path.read_text(encoding='utf-8')):
                parts = item['pronunciation']
                self.assertEqual(' и '.join(p['text'] for p in parts), item['noun'])
                for part in parts:
                    self.assertEqual(part['stressed'].replace('́', ''), part['text'])
                    if sum(c in vowels for c in part['text']) > 1:
                        self.assertEqual(part['ipa'].count('ˈ'), 1)
                        self.assertTrue('́' in part['stressed'] or 'ё' in part['stressed'])

    def test_ipa_stressed_syllable_matches_written_accent_in_every_word(self):
        import json
        vowels = set('аеёиоуыэюя')
        ipa_vowels = set('aʌəɛiɪɨɔuoɐe')
        for directory in ('dictation_1', 'dictation_2', 'dictation_3'):
            path = Path(settings.BASE_DIR) / 'tasks/lesson3' / directory / 'audio/words.json'
            for item in json.loads(path.read_text(encoding='utf-8')):
                for part in item['pronunciation']:
                    text, ipa = part['stressed'], part['ipa']
                    if sum(c in vowels for c in text) <= 1:
                        continue
                    accent = text.index('́') if '́' in text else text.index('ё') + 1
                    written_syllable = sum(c in vowels for c in text[:accent])
                    ipa_syllable = sum(c in ipa_vowels for c in ipa.split('ˈ')[0]) + 1
                    self.assertEqual(written_syllable, ipa_syllable, part['text'])

    def test_every_ipa_syllable_is_delimited_for_microsoft_stress(self):
        import json
        import re
        for directory in ('dictation_1', 'dictation_2', 'dictation_3'):
            path = Path(settings.BASE_DIR) / 'tasks/lesson3' / directory / 'audio/words.json'
            for item in json.loads(path.read_text(encoding='utf-8')):
                for part in item['pronunciation']:
                    ipa = part['ipa']
                    syllables = ipa.split('.')
                    for syllable in syllables:
                        self.assertEqual(len(re.findall('[aʌəɛiɪɨɔuoɐe]', syllable)), 1, part['text'])
                    if len(syllables) > 1:
                        self.assertEqual(ipa.count('ˈ'), 1, part['text'])
                        self.assertRegex(ipa, r'(^|\.)ˈ')


class SingularPluralGradingTests(SimpleTestCase):
    def test_sample_and_all_answers(self):
        from api.dictation import PLURAL_ANSWERS, SINGULAR_WORDS
        words = choose_words('AI_3_9')
        self.assertEqual(len(words), 10)
        self.assertEqual(len(set(words)), 10)
        self.assertTrue(set(words) <= set(range(1, 22)))
        for i, answer in enumerate(PLURAL_ANSWERS, 1):
            self.assertEqual(grade_answer(i, answer.upper() + '.', 'AI_3_9')['score'], 10)
            if SINGULAR_WORDS[i-1] != answer:
                self.assertEqual(grade_answer(i, SINGULAR_WORDS[i-1], 'AI_3_9')['score'], 0)
            with wave.open(str(Path(settings.BASE_DIR) / f'tasks/lesson3/dictation_3/audio/{i:02d}.wav')) as sound:
                self.assertGreater(sound.getnframes(), 0)
        self.assertEqual(grade_answer(11, 'годы', 'AI_3_9')['score'], 10)
        self.assertEqual(grade_answer(1, 'друзья братья', 'AI_3_9')['score'], 0)


@override_settings(DEBUG=True)
class SingularPluralAPITests(TestCase):
    def test_sixty_passes_fifty_fails_and_retries_are_idempotent(self):
        from api.dictation import PLURAL_ANSWERS
        call_command('seed_ai_test_data', stdout=StringIO())
        for target in (60, 50):
            run = self.client.post('/api/dictation/start', {
                'task_code': 'AI_3_9', 'student_code': TEST_STUDENT_CODE,
            }, content_type='application/json').json()
            self.assertEqual(run['word_count'], 10)
            self.assertEqual(run['item_max_score'], 10)
            self.assertNotIn('words', run)
            self.assertNotIn('expected', run['current'])
            words = Session.objects.get(pk=run['run_id']).get_decoded()['ai_dictation']['words']
            for index, word_id in enumerate(words):
                payload = {'run_id': run['run_id'], 'index': index,
                           'answer': PLURAL_ANSWERS[word_id-1] if index < target // 10 else '', 'score': 100}
                response = self.client.post('/api/dictation/answer', payload, content_type='application/json')
                self.assertEqual(response.status_code, 200)
            final = response.json()
            self.assertEqual(final['score'], target)
            self.assertEqual(final['ok'], target >= 60)
            self.assertTrue(final['saved'])
            self.client.post('/api/dictation/answer', payload, content_type='application/json')
        self.assertEqual(TaskAttempt.objects.filter(task__code='AI_3_9').count(), 2)


class DictationAudioCueTests(SimpleTestCase):
    def test_all_recordings_have_quiet_cue_then_half_second_silence(self):
        from array import array
        import sys
        for directory in ('dictation_1', 'dictation_2', 'dictation_3', 'novgorod_dictation'):
            for path in (Path(settings.BASE_DIR) / 'tasks/lesson3' / directory / 'audio').glob('*.wav'):
                with wave.open(str(path)) as sound:
                    rate = sound.getframerate()
                    channels = sound.getnchannels()
                    self.assertEqual(sound.getsampwidth(), 2)
                    samples = array('h', sound.readframes(round(rate * .65)))
                    if sys.byteorder != 'little':
                        samples.byteswap()
                    cue_end = round(rate * .15) * channels
                    cue = samples[:cue_end]
                    silence = samples[cue_end:]
                    self.assertGreater(max(abs(x) for x in cue), 500, str(path))
                    self.assertLessEqual(max(abs(x) for x in cue), 1036, str(path))
                    self.assertEqual(cue[0], 0)
                    self.assertEqual(cue[-1], 0)
                    self.assertLess(max(abs(x) for x in silence), 100, str(path))
                    speech = array('h', sound.readframes(sound.getnframes()))
                    self.assertTrue(any(speech), str(path))


class NovgorodDictationTests(SimpleTestCase):
    def test_order_word_count_and_word_edit_scoring(self):
        from api.dictation import NOVGOROD_SENTENCES, NOVGOROD_WORD_COUNT, run_score
        self.assertEqual(choose_words('AI_3_10'), list(range(1, 11)))
        self.assertEqual(NOVGOROD_WORD_COUNT, 44)
        for index, text in enumerate(NOVGOROD_SENTENCES, 1):
            item = grade_answer(index, text.upper(), 'AI_3_10')
            self.assertEqual(item['correct_words'], item['word_count'])
        for text, credited in [('Я студент.', 2), ('я студент', 2), ('Я студэнт', 1),
                               ('студент', 1), ('Я я студент', 1), ('', 0),
                               ('студент я', 0), ('Я студент Я студент', 0)]:
            with self.subTest(text=text):
                self.assertEqual(grade_answer(1, text, 'AI_3_10')['correct_words'], credited)
        self.assertEqual(run_score({'task_code': 'AI_3_10', 'answers': [{'correct_words': 26}]}), 59)
        self.assertEqual(run_score({'task_code': 'AI_3_10', 'answers': [{'correct_words': 27}]}), 61)

    def test_sentence_pronunciation_and_audio(self):
        import json
        import re
        path = Path(settings.BASE_DIR) / 'tasks/lesson3/novgorod_dictation/audio'
        words = json.loads((path / 'words.json').read_text(encoding='utf-8'))
        for item in words:
            self.assertEqual(' '.join(p['text'] for p in item['pronunciation']), item['noun'])
            for part in item['pronunciation']:
                self.assertEqual(part['stressed'].replace('́', '').casefold(), part['text'].casefold())
                for syllable in part['ipa'].split('.'):
                    self.assertEqual(len(re.findall('[aʌəɛiɪɨɔuoɐe]', syllable)), 1)
            with wave.open(str(path / f"{item['id']:02d}.wav")) as sound:
                self.assertGreater(sound.getnframes() / sound.getframerate(), .65)


@override_settings(DEBUG=True)
class NovgorodDictationAPITests(TestCase):
    def test_weighted_complete_attempt_retry_and_restore(self):
        from api.dictation import NOVGOROD_SENTENCES
        call_command('seed_ai_test_data', stdout=StringIO())
        run = self.client.post('/api/dictation/start', {
            'task_code': 'AI_3_10', 'student_code': TEST_STUDENT_CODE,
        }, content_type='application/json').json()
        self.assertEqual(run['total_words'], 44)
        self.assertEqual(run['answers'], [])
        self.assertEqual(run['current']['index'], 0)
        self.assertNotIn('expected', run['current'])
        for index, sentence in enumerate(NOVGOROD_SENTENCES):
            text = sentence if index != 0 else 'я'
            payload = {'run_id': run['run_id'], 'index': index, 'answer': text, 'score': 100}
            response = self.client.post('/api/dictation/answer', payload, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            restored = self.client.get('/api/dictation/state', {'run_id': run['run_id']}).json()
            self.assertEqual(restored['answered'], index + 1)
        final = response.json()
        self.assertEqual(final['correct_words'], 43)
        self.assertEqual(final['score'], 97)
        self.assertTrue(final['ok'])
        self.assertTrue(final['saved'])
        self.client.post('/api/dictation/answer', payload, content_type='application/json')
        attempt = TaskAttempt.objects.get(task__code='AI_3_10')
        self.assertEqual(attempt.score, 97)
        self.assertEqual(TaskAttempt.objects.filter(task__code='AI_3_10').count(), 1)


class PairDictationSingularAudioTests(SimpleTestCase):
    def test_speech_is_singular_and_grading_still_expects_plural(self):
        import json
        from api.dictation import PAIR_ANSWERS
        expected = (
            'лампа и карандаш', 'радио и газета', 'учебник и день', 'шкаф и карта',
            'портфель и тетрадь', 'пальто и костюм', 'папка и словарь', 'дом и общежитие',
            'кровать и окно', 'журнал и картина', 'слово и упражнение', 'книга и место',
            'машина и телевизор', 'брат и отец', 'мать и друг', 'сестра и товарищ',
            'дочь и преподаватель',
        )
        path = Path(settings.BASE_DIR) / 'tasks/lesson3/dictation_2/audio/words.json'
        items = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(tuple(item['noun'] for item in items), expected)
        for item, plural in zip(items, PAIR_ANSWERS):
            self.assertEqual(grade_answer(item['id'], plural, 'AI_3_8')['score'], 20)
            self.assertEqual(grade_answer(item['id'], item['noun'], 'AI_3_8')['score'], 10 if item['id'] in (2, 6) else 0)
