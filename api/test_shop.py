from io import StringIO
from pathlib import Path
import re

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE
from .reading_check import READING_TASKS
from .shop import ACCUSATIVE_INDEXES, SOURCE, WORDS


@override_settings(DEBUG=True)
class ShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_reading_uses_the_full_text_and_saves_under_its_own_code(self):
        page = (Path(settings.BASE_DIR) / 'tasks/lesson6/shop/reading.html').read_text(encoding='utf-8')
        source_html = re.search(r'<div id="source" class="source">(.*?)</div>', page, re.S)[1]
        self.assertEqual(re.findall(r'<p>(.*?)</p>', source_html), SOURCE['paragraphs'])
        self.assertIn('const MAX_SECONDS = 120;', page)
        task_id = 'lesson6_shop_reading'
        self.assertEqual(READING_TASKS[task_id]['max_duration_sec'], 120)
        response = self.client.post('/api/reading/complete', {
            'task_id': task_id, 'task_code': 'AI_6_12', 'student_code': TEST_STUDENT_CODE,
            'result': {'score': 95, 'ok': True, 'recognized': 'Вчера вечером я была в магазине.'},
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_12', score=95).exists())

    def test_accusative_distinguishes_the_two_occurrences_of_friends(self):
        correct = sorted(ACCUSATIVE_INDEXES)
        self.assertEqual(
            [WORDS[index] for index in correct],
            ['продукты', 'рубль', 'гости', 'друзей', 'Что', 'килограмм', 'пачку', 'банку', 'десяток',
             'вкусный', 'ужин', 'меня', 'интересные', 'истории', 'сто', 'сто'],
        )
        response = self.client.post('/api/shop/accusative/check', {
            'task_code': 'AI_6_16', 'student_code': TEST_STUDENT_CODE,
            'selected': correct + [len(WORDS) - 1],  # «друзей» после «сто» — родительный.
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'score': 94, 'correct': 16, 'extra': 1, 'total': 16, 'saved': True})
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_16', score=94).exists())
