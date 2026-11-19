from io import StringIO
from pathlib import Path
import re

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .biography import GENITIVE_INDEXES, SOURCE, WORDS
from .reading_check import READING_TASKS


@override_settings(DEBUG=True)
class BiographyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_reading_page_uses_the_source_and_one_minute_limit(self):
        page = (Path(settings.BASE_DIR) / 'tasks/lesson6/biography/reading.html').read_text(encoding='utf-8')
        source_html = re.search(r'<div id="source" class="source">(.*?)</div>', page, re.S)[1]
        self.assertEqual(re.findall(r'<p>(.*?)</p>', source_html), SOURCE['paragraphs'])
        task_id = 'lesson6_biography_reading'
        self.assertEqual(READING_TASKS[task_id]['max_duration_sec'], 60)
        self.assertIn('const MAX_SECONDS = 60;', page)
        response = self.client.post('/api/reading/complete', {
            'task_id': task_id, 'task_code': 'AI_6_7', 'student_code': TEST_STUDENT_CODE,
            'result': {'score': 95, 'ok': True, 'recognized': 'Володя приехал из Восточной Сибири.'},
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_7', score=95).exists())

    def test_genitive_includes_modifiers_and_excludes_the_name_in_apposition(self):
        correct = sorted(GENITIVE_INDEXES)
        self.assertEqual(
            [WORDS[index] for index in correct],
            ['Восточной', 'Сибири', 'небольшого', 'города', 'глубокого', 'красивого', 'озера',
             'первого', 'курса', 'Университета', 'инженеров', 'транспорта', 'своего', 'родного', 'города'],
        )
        response = self.client.post('/api/biography/genitive/check', {
            'task_code': 'AI_6_8', 'student_code': TEST_STUDENT_CODE,
            'selected': correct + [WORDS.index('Байкал')],
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'score': 93, 'correct': 15, 'extra': 1, 'total': 15, 'saved': True})
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_8', score=93).exists())
