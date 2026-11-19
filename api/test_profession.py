from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .profession import ACCUSATIVE_INDEXES, QUESTION_BANK, WORDS
from .reading_check import READING_TASKS
from .university_questions import AnswerGrade


@override_settings(DEBUG=True)
class ProfessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_accusative_uses_occurrences_and_saves_its_score(self):
        correct = sorted(ACCUSATIVE_INDEXES)
        self.assertEqual(
            [WORDS[index] for index in correct],
            ['Петербург', 'улицы', 'площади', 'парки', 'статьи', 'фотографии',
             'Лейлу', 'книги', 'подарки', 'Красную', 'площадь', 'Исторический',
             'музей', 'хорошую', 'подругу'],
        )
        nominative = max(index for index, word in enumerate(WORDS) if word == 'фотографии')
        body = {'task_code': 'AI_6_2', 'student_code': TEST_STUDENT_CODE, 'selected': correct + [nominative]}
        response = self.client.post('/api/profession/accusative/check', body, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'score': 93, 'correct': 15, 'extra': 1, 'total': 15, 'saved': True})
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_2', score=93).exists())

    def test_reading_completion_checks_the_task_code(self):
        task_id = 'lesson6_profession_reading'
        self.assertIn('Мы вместе работаем', READING_TASKS[task_id]['reference_text'])
        body = {'task_id': task_id, 'task_code': 'AI_6_2', 'student_code': TEST_STUDENT_CODE,
                'result': {'score': 95, 'ok': True, 'recognized': 'Меня зовут Олег.'}}
        response = self.client.post('/api/reading/complete', body, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        body['task_code'] = 'AI_6_1'
        response = self.client.post('/api/reading/complete', body, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_1', score=95).exists())

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.university_questions._get_agent')
    def test_written_questions_run_in_order_and_save_the_final_score(self, get_agent):
        def post(path, body):
            response = self.client.post(f'/api/university-questions/{path}', body, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            return response.json()

        grader = get_agent.return_value.run_sync
        grader.return_value.output = AnswerGrade(
            content_correct=True, writing_correct=True, content_feedback='Верно.',
            writing_feedback='Без ошибок.', corrected_answer='',
        )
        state = post('start', {'task_code': 'AI_6_3', 'student_code': TEST_STUDENT_CODE})
        self.assertEqual(state['word_count'], 10)
        self.assertEqual(state['current']['question'], 'Кто такой Олег?')

        for index, (question, _, example) in enumerate(QUESTION_BANK):
            self.assertEqual(state['current'], {'index': index, 'question': question, 'audio_path': None})
            state = post('answer', {'run_id': state['run_id'], 'index': index, 'answer': example if index < 6 else ''})
        self.assertEqual(grader.call_count, 6)
        self.assertEqual(state['score'], 60)
        self.assertTrue(state['completed'])
        self.assertTrue(state['ok'])
        self.assertTrue(state['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_3', score=60).exists())
