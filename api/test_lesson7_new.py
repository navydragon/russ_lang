from io import StringIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from api.reading_check import READING_TASKS, check_reading_audio, score_reading_from_payload
from api.story_llm import StoryCheckResult
from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE


@override_settings(DEBUG=True)
class NewLesson7Tests(TestCase):
    def setUp(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def result(self):
        return StoryCheckResult(ok=True, score=80, normalized='Ответ', feedback='Проверено', errors=[], recommendations=[], quality_notes='')

    def test_reading_sources_and_independent_saves(self):
        for name, number in (('vdnh', 7), ('fairytale', 8), ('gagarin', 9)):
            task_id = f'lesson7_{name}_reading'
            task = READING_TASKS[task_id]
            self.assertEqual(task['max_duration_sec'], 120)
            payload = {'text': task['reference_text'], 'duration': 119}
            result = score_reading_from_payload(payload, task['reference_text'], max_duration_sec=120)
            self.assertGreaterEqual(result['coverage']['ratio'], .99)
            response = self.client.post('/api/reading/complete', {
                'task_id': task_id, 'task_code': f'AI_7_{number}', 'student_code': TEST_STUDENT_CODE,
                'result': {'ok': True, 'score': 89.5, 'recognized': 'текст'},
            }, content_type='application/json')
            self.assertTrue(response.json()['saved'])
            self.assertTrue(TaskAttempt.objects.filter(task__code=f'AI_7_{number}').exists())
        self.assertNotIn('Красную площадь', READING_TASKS['lesson7_gagarin_reading']['reference_text'])

    def test_reading_checks_route_and_failures(self):
        for name in ('vdnh', 'fairytale', 'gagarin'):
            task_id = f'lesson7_{name}_reading'
            payload = {'ok': True, 'score': 90, 'recognized': 'текст'}
            with patch('api.views.check_reading_audio', return_value=payload) as checker:
                response = self.client.post('/api/reading/check', {'task_id': task_id, 'file': SimpleUploadedFile('reading.webm', b'audio')})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(checker.call_args.kwargs['task_id'], task_id)
            with patch('api.views.check_reading_audio', side_effect=ValueError('Речь не распознана')):
                response = self.client.post('/api/reading/check', {'task_id': task_id, 'file': SimpleUploadedFile('reading.webm', b'audio')})
            self.assertEqual(response.status_code, 400)

    def test_writing_and_verbs_save_under_own_codes_and_failure(self):
        for task_id, code in (('lesson7_fairytale_verbs', 'AI_7_10'), ('lesson7_faculty_writing', 'AI_7_12')):
            body = {'task_id': task_id, 'task_code': code, 'student_code': TEST_STUDENT_CODE, 'text': 'Ответ'}
            with patch('api.views.check_story', return_value=self.result()):
                response = self.client.post('/api/story/check', body, content_type='application/json')
            self.assertTrue(response.json()['saved'])
            self.assertTrue(TaskAttempt.objects.filter(task__code=code).exists())
            body['task_code'] = 'AI_7_1'
            self.assertEqual(self.client.post('/api/story/check', body, content_type='application/json').status_code, 400)
        with patch('api.views.check_story', side_effect=RuntimeError('Нет сервиса')):
            response = self.client.post('/api/story/check', {'task_id': 'lesson7_faculty_writing', 'task_code': 'AI_7_12', 'text': 'Ответ'}, content_type='application/json')
        self.assertEqual(response.status_code, 500)

    def test_gagarin_dates_recognized_as_digits(self):
        text = READING_TASKS['lesson7_gagarin_reading']['reference_text']
        substitutions = {
            'Двенадцатого': '12', 'двенадцатого': '12',
            'тысяча девятьсот шестьдесят первого': '1961',
            'тысяча девятьсот шестьдесят восьмого': '1968',
            'двадцать седьмого': '27', 'сто восемь': '108',
            'девять': '9', 'семь': '07',
        }
        for source, replacement in substitutions.items():
            text = text.replace(source, replacement)
        with patch('api.reading_check.transcribe_audio', return_value={'text': text}), patch('api.reading_check.measure_audio_duration', return_value=90):
            result = check_reading_audio(b'audio', 'reading.webm', task_id='lesson7_gagarin_reading')
        self.assertGreaterEqual(result['coverage']['ratio'], .99)

    def test_retelling_saved(self):
        speech = {'recognized': 'Ответ', 'duration': 30, 'passing_score': 60, 'stress_check': {'status': 'not_assessed'}}
        with patch('api.views.check_retelling_audio', return_value=(self.result(), speech)):
            response = self.client.post('/api/retelling/check', {'task_id': 'lesson7_fairytale_retelling', 'task_code': 'AI_7_11', 'student_code': TEST_STUDENT_CODE, 'file': SimpleUploadedFile('x.webm', b'audio')})
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_7_11').exists())
