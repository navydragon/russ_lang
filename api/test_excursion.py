import json
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.contrib.sessions.backends.db import SessionStore

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .excursion import SOURCE, REFERENCE_TEXT, score_selection, words_and_targets
from .reading_check import READING_TASKS
from .university_questions import TASKS


class ExcursionSourceTests(SimpleTestCase):
    def test_shared_json_is_served_to_task_pages(self):
        response = self.client.get('/tasks/lesson7/excursion_text.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(b''.join(response.streaming_content))['questions'], SOURCE['questions'])

    def test_full_text_and_four_questions_are_shared_by_three_tasks(self):
        self.assertIn('На метро каждый москвич экономит 240 часов в год', REFERENCE_TEXT)
        self.assertIn('Летом в метро 20 градусов', REFERENCE_TEXT)
        self.assertEqual(len(SOURCE['questions']), 4)
        self.assertEqual(READING_TASKS['excursion_moscow']['max_duration_sec'], 300)
        self.assertEqual(READING_TASKS['excursion_moscow']['reference_text'], REFERENCE_TEXT)
        self.assertEqual(TASKS['AI_7_4']['count'], 4)

    def test_highlight_targets_and_penalty(self):
        words, targets = words_and_targets()
        self.assertIn(words.index('квадратных'), targets['genitive_plural'])
        self.assertIn(words.index('Летом'), targets['time'])
        selected = {key: sorted(values) for key, values in targets.items()}
        self.assertEqual(score_selection(selected)['score'], 100)
        self.assertEqual(score_selection({'genitive_plural': selected['genitive_plural'], 'time': []})['score'], 50)
        selected['genitive_plural'].append(words.index('Москва'))
        self.assertLess(score_selection(selected)['score'], 100)
        with self.assertRaises(ValueError):
            score_selection({'genitive_plural': [len(words)], 'time': []})


@override_settings(DEBUG=True)
class ExcursionEndpointTests(TestCase):
    def setUp(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_highlight_is_scored_and_saved_under_its_own_code(self):
        _, targets = words_and_targets()
        response = self.client.post('/api/excursion/highlight/check', data=json.dumps({
            'task_code': 'AI_7_2', 'student_code': TEST_STUDENT_CODE,
            'selected': {name: sorted(indexes) for name, indexes in targets.items()},
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['score'], 100)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_7_2', score=100).exists())

    def test_four_answer_run_normalizes_to_100_and_saves(self):
        start = self.client.post('/api/university-questions/start', data=json.dumps({
            'task_code': 'AI_7_4', 'student_code': TEST_STUDENT_CODE,
        }), content_type='application/json').json()
        self.assertEqual(start['word_count'], 4)
        self.assertIsNone(start['current']['audio_path'])
        with patch('api.university_question_views.grade_answer') as grader:
            for index in range(4):
                grader.return_value = {'answer': f'Ответ {index}', 'score': 10,
                                       'content_points': 5, 'writing_points': 5}
                response = self.client.post('/api/university-questions/answer', data=json.dumps({
                    'run_id': start['run_id'], 'index': index, 'answer': f'Ответ {index}',
                }), content_type='application/json')
                self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertTrue(state['completed'])
        self.assertEqual(state['score'], 100)
        self.assertTrue(state['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_7_4', score=100).exists())

    def test_seven_faculty_answers_and_old_sessions(self):
        start = self.client.post('/api/university-questions/start', {
            'task_code': 'AI_7_6', 'student_code': TEST_STUDENT_CODE,
        }, content_type='application/json').json()
        self.assertEqual(start['word_count'], 7)
        with patch('api.university_question_views.grade_answer') as grader:
            for index in range(7):
                grader.return_value = {'answer': 'Ответ', 'question': 'Вопрос', 'score': 10}
                response = self.client.post('/api/university-questions/answer', {
                    'run_id': start['run_id'], 'index': index, 'answer': 'Ответ',
                }, content_type='application/json')
                self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['score'], 100)
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_7_6', score=100).exists())

        for completed in (False, True):
            store = SessionStore()
            store['ai_university_questions'] = {
                'task_code': 'AI_7_4', 'student_code': TEST_STUDENT_CODE,
                'words': list(range(1, 7)),
                'answers': [{'answer': 'Ответ', 'question': 'Старый вопрос', 'score': 10}] * (6 if completed else 1),
                'saved': completed,
            }
            store.create()
            response = self.client.get('/api/university-questions/state', {'run_id': store.session_key})
            if completed:
                self.assertEqual(response.json()['score'], 100)
                self.assertTrue(response.json()['completed'])
            else:
                self.assertEqual(response.status_code, 409)
                self.assertTrue(response.json()['restart_required'])
                response = self.client.post('/api/university-questions/answer', {
                    'run_id': store.session_key, 'index': 1, 'answer': 'Ответ',
                }, content_type='application/json')
                self.assertEqual(response.status_code, 409)

    def test_reading_route_and_completion_save_under_ai_7_3(self):
        result = {'ok': True, 'score': 83, 'recognized': 'Экскурсия по Москве',
                  'duration': 250, 'coverage': {'ratio': 0.9}, 'pauses': {'score': 7}}
        with patch('api.views.check_reading_audio', return_value=result) as checker:
            response = self.client.post('/api/reading/check', data={
                'task_id': 'excursion_moscow',
                'file': SimpleUploadedFile('reading.webm', b'audio', content_type='audio/webm'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(checker.call_args.kwargs['task_id'], 'excursion_moscow')
        complete = self.client.post('/api/reading/complete', data=json.dumps({
            'task_id': 'excursion_moscow', 'task_code': 'AI_7_3',
            'student_code': TEST_STUDENT_CODE, 'result': result,
        }), content_type='application/json')
        self.assertTrue(complete.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_7_3', score=83).exists())
