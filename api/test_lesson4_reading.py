import math
from pathlib import Path
import re
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from io import StringIO

from api.reading_check import (
    LESSON4_UNIVERSITY_REFERENCE_PARTS,
    LESSON4_UNIVERSITY_REFERENCE_TEXT as FULL_REFERENCE,
    READING_TASKS,
    align_reference_with_gaps,
    build_reading_correct_prompt,
    check_reading_audio,
    score_reading_from_payload,
    sentence_boundary_token_indices,
)
from api.speaking_nexara import tokenize_ru
from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE


REFERENCE = LESSON4_UNIVERSITY_REFERENCE_PARTS[0]

def payload(gap=.4, duration=400, reference=REFERENCE):
    words = []
    time = 0.0
    for match in re.finditer(r'\w+|[.?!]', reference):
        word = match.group()
        if word in '.?!':
            time += gap
        else:
            words.append({'word': word, 'start': time, 'end': time + .2})
            time += .25
    return {'text': reference, 'words': words, 'duration': duration}


class LessonFourReadingTests(SimpleTestCase):
    def check(self, source):
        with patch('api.reading_check.transcribe_audio', return_value=source) as asr:
            result = check_reading_audio(b'audio', 'record.webm', task_id='lesson4_university')
        self.assertTrue(asr.call_args.kwargs['word_timestamps'])
        self.assertIn('играют в футбол тут.', asr.call_args.kwargs['prompt'])
        self.assertNotIn('Слева находится наша библиотека', asr.call_args.kwargs['prompt'])
        return result

    def test_both_source_slides_are_included_without_other_university_text(self):
        self.assertEqual(len(LESSON4_UNIVERSITY_REFERENCE_PARTS), 2)
        for text in ('Это Антон, Виктор и Андрей', 'Вы всё понимаете?', 'играют в баскетбол',
                     'Слева находится наша библиотека', 'суп, борщ, салат'):
            self.assertIn(text, FULL_REFERENCE)
        self.assertIn('наша комната № 5', FULL_REFERENCE)
        self.assertIn('Мы любим наш университет.', build_reading_correct_prompt(FULL_REFERENCE))
        self.assertNotIn('механический факультет', REFERENCE)

    def test_complete_reading_has_no_time_limit_and_no_fabricated_acoustic_checks(self):
        for duration in (400, None):
            result = self.check(payload(duration=duration))
            self.assertTrue(result['ok'], result)
            self.assertIsNone(result['duration_check']['max_sec'])
            self.assertFalse(result['duration_check']['required'])
            self.assertEqual(result['coverage']['min_ratio'], .6)
            self.assertEqual(set(result['assessment_limits'].values()), {'not_assessed'})

    def test_dialogue_questions_are_real_pause_boundaries(self):
        boundaries = sentence_boundary_token_indices(REFERENCE, '.?!')
        self.assertTrue(any(item['punctuation'] == '?' for item in boundaries))
        self.assertFalse(self.check(payload(gap=.05))['pauses']['ok'])
        self.assertTrue(self.check(payload())['pauses']['ok'])

    def test_coverage_threshold_and_missing_timestamps(self):
        distinct = sorted(set(tokenize_ru(REFERENCE)))
        for size, expected in ((math.ceil(len(distinct)*.6), True), (math.ceil(len(distinct)*.6)-1, False)):
            source = payload()
            source['text'] = ' '.join(distinct[:size])
            self.assertEqual(self.check(source)['coverage']['ok'], expected)
        source = payload()
        source.pop('words')
        self.assertFalse(self.check(source)['ok'])

    def test_missing_word_does_not_discard_later_alignment(self):
        words = payload()['words']
        del words[1]
        aligned = align_reference_with_gaps(REFERENCE, words)
        self.assertIsNotNone(aligned[-1])
        self.assertEqual(aligned[-1]['word'], 'тут')

    def test_original_audio_and_both_provenance_screenshots_are_present(self):
        task = Path(settings.BASE_DIR) / 'tasks/lesson4/university_reading'
        for name in ('reference.wav', 'reference-part-1.mp3', 'reference-part-2.mp3', 'source-slide-35.png',
                     'source-slide-36.png', 'university.png'):
            self.assertGreater((task / name).stat().st_size, 1000)
        page = (task / 'university_reading.html').read_text(encoding='utf-8')
        self.assertIn('const TASK_CODE = "AI_4_1";', page)
        self.assertNotIn('MAX_RECORD_SEC', page)
        self.assertNotIn('3 минуты', page)

    def test_endpoint_uses_lesson_four_reference(self):
        with patch('api.reading_check.transcribe_audio', return_value=payload()):
            response = self.client.post('/api/reading/check', {
                'task_id': 'lesson4_university', 'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertIsNone(response.json()['duration_check']['max_sec'])


@override_settings(DEBUG=True)
class LessonFourReadingPersistenceTests(TestCase):
    def test_result_saves_to_lesson_four_and_source_audio_is_served(self):
        call_command('seed_ai_test_data', stdout=StringIO())
        with patch('api.reading_check.transcribe_audio', return_value=payload()):
            result = check_reading_audio(b'audio', 'record.webm', task_id='lesson4_university')
        response = self.client.post('/api/reading/complete', {
            'task_id': 'lesson4_university', 'task_code': 'AI_4_1',
            'student_code': TEST_STUDENT_CODE, 'result': result,
        }, content_type='application/json')
        self.assertTrue(response.json()['saved'])
        self.assertEqual(TaskAttempt.objects.get().task.lesson.position, 4)
        for index in (1, 2):
            response = self.client.get(f'/tasks/lesson4/university_reading/reference-part-{index}.mp3')
            self.assertEqual(response.status_code, 200)
            response.close()


@override_settings(DEBUG=True)
class LessonFourSplitReadingTests(TestCase):
    def test_separate_references_second_reading_and_second_result(self):
        first = READING_TASKS['lesson4_university']['reference_text']
        second = READING_TASKS['lesson4_university_part2']['reference_text']
        self.assertNotIn('Слева находится наша библиотека', first)
        self.assertNotIn('Анна спрашивает', second)
        self.assertEqual(second, LESSON4_UNIVERSITY_REFERENCE_PARTS[1])
        call_command('seed_ai_test_data', stdout=StringIO())
        with patch('api.reading_check.transcribe_audio', return_value=payload(reference=second)) as asr:
            result = check_reading_audio(b'audio', 'record.webm', task_id='lesson4_university_part2')
        self.assertTrue(result['ok'])
        self.assertIn('Мы любим наш университет.', asr.call_args.kwargs['prompt'])
        self.assertNotIn('Анна спрашивает', asr.call_args.kwargs['prompt'])
        response = self.client.post('/api/reading/complete', {
            'task_id': 'lesson4_university_part2', 'task_code': 'AI_4_15',
            'student_code': TEST_STUDENT_CODE, 'result': result,
        }, content_type='application/json')
        self.assertTrue(response.json()['saved'])
        self.assertEqual(TaskAttempt.objects.get().task.code, 'AI_4_15')
        self.assertEqual(TaskAttempt.objects.get().task.lesson.position, 4)

    def test_stresses_preserve_original_and_cover_every_multisyllabic_word(self):
        import json
        from scripts.generate_yandex_dictation_audio import mark_stress
        from scripts.generate_yandex_reading_audio import reading_chunks
        bank = json.loads((Path(settings.BASE_DIR) / 'tasks/lesson4/university_reading/yandex-reading.json').read_text(encoding='utf-8'))
        for part in bank['parts']:
            self.assertEqual(part['stressed_text'].replace('́', ''), part['text'])
            self.assertEqual(part['text'], LESSON4_UNIVERSITY_REFERENCE_PARTS[part['id']-1])
            for word in part['pronunciation']:
                if sum(c.lower() in 'аеёиоуыэюя' for c in word['text']) > 1:
                    self.assertTrue('ё' in word['text'].lower() or word['stressed'].count('́') == 1, word)
            marked = mark_stress(part['text'], part['pronunciation'])
            chunks = reading_chunks(marked)
            self.assertTrue(all(len(chunk) <= 180 for chunk in chunks))
            self.assertEqual(' '.join(chunks), ' '.join(marked.split()))
        marked = mark_stress(bank['parts'][1]['text'], bank['parts'][1]['pronunciation'])
        for correct in ('словар+и', 'п+ишут', '+учат', 'помог+ают', 'бр+юки', 'пальт+о', 'оде+яло'):
            self.assertIn(correct, marked)
