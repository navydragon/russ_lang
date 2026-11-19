from io import StringIO
from pathlib import Path
import re

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .kremlin import GENITIVE_INDEXES, SOURCE, WORDS
from .reading_check import READING_TASKS


@override_settings(DEBUG=True)
class KremlinTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_reading_has_two_minutes_and_saves_under_its_own_code(self):
        page = (Path(settings.BASE_DIR) / 'tasks/lesson6/kremlin/reading.html').read_text(encoding='utf-8')
        source_html = re.search(r'<div id="source" class="source">(.*?)</div>', page, re.S)[1]
        self.assertEqual(re.findall(r'<p>(.*?)</p>', source_html), SOURCE['paragraphs'])
        self.assertIn('const MAX_SECONDS = 120;', page)
        task_id = 'lesson6_kremlin_reading'
        task = READING_TASKS[task_id]
        self.assertEqual(task['max_duration_sec'], 120)
        self.assertIn('Головей в 1625 году', task['reference_text'])
        self.assertIn('в 1851 году,', task['reference_text'])
        self.assertNotIn('тысяча', task['reference_text'])

        response = self.client.post('/api/reading/complete', {
            'task_id': task_id, 'task_code': 'AI_6_9', 'student_code': TEST_STUDENT_CODE,
            'result': {'score': 95, 'ok': True, 'recognized': 'Миллионы людей знают Московский Кремль.'},
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_9', score=95).exists())

    def test_genitive_checks_measurements_and_the_omitted_noun(self):
        correct = sorted(GENITIVE_INDEXES)
        self.assertEqual(
            [WORDS[index] for index in correct],
            ['людей', 'Кремля', 'Москвы', 'метров', 'сантиметров', 'сантиметра',
             'часовой', 'стрелки', 'метра', 'сантиметров', 'минутной', 'метра', 'сантиметров'],
        )
        response = self.client.post('/api/kremlin/genitive/check', {
            'task_code': 'AI_6_10', 'student_code': TEST_STUDENT_CODE,
            'selected': correct + [WORDS.index('России')],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'score': 92, 'correct': 13, 'extra': 1, 'total': 13, 'saved': True})
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_10', score=92).exists())
