from io import StringIO
from pathlib import Path
import re
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .arbat import GENITIVE_INDEXES, QUESTION_BANK, SOURCE, WORDS
from .reading_check import READING_TASKS
from .university_questions import AnswerGrade


@override_settings(DEBUG=True)
class ArbatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_reading_page_and_server_use_both_parts_of_the_text(self):
        page = (Path(settings.BASE_DIR) / 'tasks/lesson6/arbat/reading.html').read_text(encoding='utf-8')
        source_html = re.search(r'<div id="source" class="source">(.*?)</div>', page, re.S)[1]
        self.assertEqual(re.findall(r'<p>(.*?)</p>', source_html), SOURCE['paragraphs'])
        task_id = 'lesson6_arbat_reading'
        settings_for_task = READING_TASKS[task_id]
        self.assertIn('Современный Арбат', settings_for_task['reference_text'])
        self.assertEqual(settings_for_task['max_duration_sec'], 300)
        self.assertIn('const MAX_SECONDS = 300;', page)

        response = self.client.post('/api/reading/complete', {
            'task_id': task_id, 'task_code': 'AI_6_4', 'student_code': TEST_STUDENT_CODE,
            'result': {'score': 95, 'ok': True, 'recognized': 'Арбат — необычная улица.'},
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_4', score=95).exists())

    def test_genitive_scores_and_saves_the_occurrences_from_both_parts(self):
        correct = sorted(GENITIVE_INDEXES)
        self.assertEqual(
            [WORDS[index] for index in correct],
            ['Москвы', 'Кремля', 'Арбата', 'истории', 'архитектуры', 'Пушкина', 'Москвы',
             'имени', 'Вахтангова', 'имени', 'Михаила', 'Семёновича', 'Щепкина', 'транспорта', 'столицы'],
        )
        response = self.client.post('/api/arbat/genitive/check', {
            'task_code': 'AI_6_15', 'student_code': TEST_STUDENT_CODE, 'selected': correct,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'score': 100, 'correct': 15, 'extra': 0, 'total': 15, 'saved': True})
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_15', score=100).exists())

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.university_questions._get_agent')
    def test_nine_questions_are_scored_out_of_100_and_saved(self, get_agent):
        def post(path, data):
            response = self.client.post(f'/api/university-questions/{path}', data, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            return response.json()

        grader = get_agent.return_value.run_sync
        grader.return_value.output = AnswerGrade(
            content_correct=True, writing_correct=True, content_feedback='Верно.',
            writing_feedback='Без ошибок.', corrected_answer='',
        )
        state = post('start', {'task_code': 'AI_6_5', 'student_code': TEST_STUDENT_CODE})
        self.assertEqual(state['word_count'], 9)
        self.assertEqual(state['current']['question'], 'Где находится Арбат?')
        for index, (question, _, example) in enumerate(QUESTION_BANK):
            self.assertEqual(state['current'], {'index': index, 'question': question, 'audio_path': None})
            state = post('answer', {'run_id': state['run_id'], 'index': index, 'answer': example if index < 6 else ''})

        self.assertEqual(grader.call_count, 6)
        self.assertEqual(state['score'], 67)
        self.assertTrue(state['completed'])
        self.assertTrue(state['ok'])
        self.assertTrue(state['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_5', score=67).exists())
