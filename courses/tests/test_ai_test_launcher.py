from io import StringIO
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from courses.models import Course, Lesson, StudentTask, Task, TaskAttempt
from courses.task_catalog import TASK_CATALOG, TEST_COURSE_NAME, TEST_STUDENT_CODE
from students.models import Group, Student


class _TaskAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.references.extend(attributes[key] for key in ('src', 'href') if attributes.get(key))


@override_settings(DEBUG=True)
class AITestLauncherTests(TestCase):
    def seed(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def test_seed_is_repeatable_and_preserves_attempts(self):
        self.seed()
        student = Student.objects.get(code=TEST_STUDENT_CODE)
        task = Task.objects.get(code='AI_1_1')
        from django.utils import timezone
        attempt = TaskAttempt.objects.create(
            student=student, task=task, datetime=timezone.now(), score=70,
        )
        self.seed()
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Lesson.objects.count(), 4)
        self.assertEqual(Task.objects.count(), 34)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Group.objects.count(), 1)
        self.assertTrue(TaskAttempt.objects.filter(pk=attempt.pk, score=70).exists())

    def test_conflicting_real_task_is_not_modified(self):
        course = Course.objects.create(name='Реальный курс')
        lesson = Lesson.objects.create(course=course, name='Урок', position=1)
        task = Task.objects.create(lesson=lesson, name='Задание', code='AI_1_1', position=1)
        with self.assertRaises(CommandError):
            self.seed()
        task.refresh_from_db()
        self.assertEqual(task.name, 'Задание')
        self.assertFalse(Course.objects.filter(name=TEST_COURSE_NAME).exists())
        self.assertFalse(Student.objects.filter(code=TEST_STUDENT_CODE).exists())

    def test_launcher_sets_cookie_and_links_available_pages(self):
        self.seed()
        response = self.client.get('/dev/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies['student_code'].value, TEST_STUDENT_CODE)
        self.assertEqual(response.cookies['student_code']['path'], '/')
        self.assertFalse(response.cookies['student_code']['httponly'])
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertContains(response, 'Открыть задание', count=33)
        for definition in TASK_CATALOG:
            if definition.html_path:
                self.assertContains(response, '/tasks/' + definition.html_path)
                page = self.client.get('/tasks/' + definition.html_path)
                self.assertEqual(page.status_code, 200)
                page.close()
                source = (Path(settings.BASE_DIR) / 'tasks' / definition.html_path).read_text(encoding='utf-8')
                self.assertIn(f'const TASK_CODE = "{definition.code}";', source)
                self.assertIn('const API = window.ANALYZER_CONFIG.apiBaseUrl;', source)

    def test_launcher_without_seed_disables_launches(self):
        response = self.client.get('/dev/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'seed_ai_test_data')
        self.assertNotContains(response, 'Открыть задание')

    def test_every_ready_task_uses_shared_launch_config_and_has_local_assets(self):
        root = Path(settings.BASE_DIR) / 'tasks'
        for definition in TASK_CATALOG:
            if not definition.html_path:
                continue
            with self.subTest(task=definition.code):
                page = root / definition.html_path
                html = page.read_text(encoding='utf-8')
                self.assertIn('../../api-config.js', html)
                self.assertIn('const API = window.ANALYZER_CONFIG.apiBaseUrl;', html)
                self.assertIn(f'const TASK_CODE = "{definition.code}";', html)
                parser = _TaskAssetParser()
                parser.feed(html)
                for reference in parser.references:
                    parsed = urlsplit(reference)
                    if parsed.scheme or reference.startswith(('/', '#', 'data:')):
                        continue
                    asset = (page.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(asset.is_relative_to(root.resolve()))
                    self.assertTrue(asset.is_file(), f'Missing {reference} for {definition.code}')

    @override_settings(DEBUG=False)
    def test_test_tools_disabled_outside_debug(self):
        self.assertEqual(self.client.get('/dev/tasks/').status_code, 404)
        with self.assertRaises(CommandError):
            self.seed()
        self.assertEqual(Student.objects.count(), 0)

    def test_story_result_is_saved_for_test_student_and_shown_in_launcher(self):
        self.seed()
        self.client.get('/dev/tasks/')
        code = self.client.cookies['student_code'].value
        result = SimpleNamespace(model_dump=lambda: {
            'ok': True, 'score': 100, 'feedback': 'Хорошо',
            'normalized': 'Это мама. Это папа. Это брат.',
            'errors': [], 'quality_notes': 'Связный текст', 'recommendations': [],
        })
        with patch('api.views.check_story', return_value=result):
            response = self.client.post('/api/story/check', {
                'task_id': 'family', 'task_code': 'AI_1_1',
                'student_code': code, 'text': 'Это мама. Это папа. Это брат.',
            }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        attempt = TaskAttempt.objects.get()
        self.assertEqual(attempt.student.code, TEST_STUDENT_CODE)
        self.assertEqual(attempt.task.code, 'AI_1_1')
        self.assertTrue(StudentTask.objects.filter(student=attempt.student, task=attempt.task).exists())
        response = self.client.get('/dev/tasks/')
        self.assertContains(response, 'зачтено')
        self.assertEqual(len(response.context['attempts']), 1)

    def test_speaking_and_reading_results_are_saved_with_catalog_codes(self):
        self.seed()
        for code, task_id in [('AI_1_3', 'city'), ('AI_1_4', 'class'), ('AI_1_5', 'flat')]:
            response = self.client.post('/api/speaking/complete', {
                'student_code': TEST_STUDENT_CODE, 'task_code': code,
                'task_id': task_id, 'steps': [{'reference': 'слово'}] * 3,
            }, content_type='application/json')
            self.assertTrue(response.json()['saved'], response.content)
        response = self.client.post('/api/reading/complete', {
            'student_code': TEST_STUDENT_CODE, 'task_code': 'AI_3_1',
            'task_id': 'university', 'result': {'ok': True, 'recognized': 'Тест чтения'},
        }, content_type='application/json')
        self.assertTrue(response.json()['saved'], response.content)
        self.assertEqual(TaskAttempt.objects.count(), 4)

    def test_photo_album_result_saves_to_lesson_two(self):
        self.seed()
        response = self.client.post('/api/reading/complete', {
            'student_code': TEST_STUDENT_CODE, 'task_code': 'AI_2_1',
            'task_id': 'photo_album', 'result': {
                'ok': True, 'recognized': 'Это я. Это моя семья.',
                'duration': 45, 'pauses': {'ok': True},
            },
        }, content_type='application/json')
        self.assertTrue(response.json()['saved'])
        attempt = TaskAttempt.objects.get(task__code='AI_2_1')
        self.assertEqual(attempt.task.lesson.position, 2)
        self.assertEqual(attempt.student.code, TEST_STUDENT_CODE)

    def test_family_photo_text_saves_with_separate_lesson_two_code(self):
        self.seed()
        result = SimpleNamespace(model_dump=lambda: {
            'ok': True, 'score': 95, 'feedback': 'Хорошо',
            'normalized': 'Это мой отец. Его зовут Иван. Он врач.',
            'errors': [], 'quality_notes': 'Рассказ о семье', 'recommendations': [],
        })
        with patch('api.views.check_story', return_value=result) as check:
            response = self.client.post('/api/story/check', {
                'task_id': 'family_retelling', 'task_code': 'AI_2_2',
                'student_code': TEST_STUDENT_CODE,
                'text': 'Это мой отец. Его зовут Иван. Он врач.',
            }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(check.call_args.args[0], 'family_retelling')
        self.assertEqual(TaskAttempt.objects.get().task.code, 'AI_2_2')
        self.assertEqual(TaskAttempt.objects.get().task.lesson.position, 2)

    def test_oral_retelling_saves_both_pass_and_fail_with_audio_metadata(self):
        from api.test_retelling import retelling_result
        from django.core.files.uploadedfile import SimpleUploadedFile
        import json
        self.seed()
        for score in (59, 60):
            result = retelling_result(score)
            speech = {
                'recognized': 'Вот наш университет.', 'duration': 35, 'passing_score': 60,
                'stress_check': {'status': 'not_assessed'},
            }
            with patch('api.views.check_retelling_audio', return_value=(result, speech)):
                response = self.client.post('/api/retelling/check', {
                    'task_id': 'university_retelling', 'task_code': 'AI_3_2',
                    'student_code': TEST_STUDENT_CODE,
                    'file': SimpleUploadedFile('record.webm', b'audio'),
                })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['saved'])
            attempt = TaskAttempt.objects.order_by('-pk').first()
            self.assertEqual(attempt.task.code, 'AI_3_2')
            self.assertEqual(attempt.is_completed, score >= 60)
            saved = json.loads(attempt.results)
            self.assertEqual(saved['source'], 'retelling_check')
            self.assertEqual(saved['speech_assessment']['stress_check']['status'], 'not_assessed')

    def test_my_university_writing_saves_under_ai_3_4(self):
        self.seed()
        text = 'Мой университет большой. Здесь хорошая библиотека.'
        result = SimpleNamespace(model_dump=lambda: {
            'ok': True, 'score': 75, 'feedback': 'Хорошо', 'normalized': text,
            'errors': [], 'quality_notes': 'Связный рассказ', 'recommendations': [],
        })
        with patch('api.views.check_story', return_value=result) as check:
            response = self.client.post('/api/story/check', {
                'task_id': 'my_university_story', 'task_code': 'AI_3_4',
                'student_code': TEST_STUDENT_CODE, 'text': text,
            }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(check.call_args.args, ('my_university_story', text))
        attempt = TaskAttempt.objects.get()
        self.assertEqual(attempt.task.code, 'AI_3_4')
        self.assertEqual(attempt.task.lesson.position, 3)

    def test_moscow_reading_saves_under_ai_3_5(self):
        self.seed()
        response = self.client.post('/api/reading/complete', {
            'student_code': TEST_STUDENT_CODE, 'task_code': 'AI_3_5', 'task_id': 'moscow',
            'result': {'ok': True, 'recognized': 'Москва — большой и красивый город.'},
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        attempt = TaskAttempt.objects.get()
        self.assertEqual(attempt.task.code, 'AI_3_5')
        self.assertEqual(attempt.task.lesson.position, 3)

    def test_moscow_retelling_saves_under_ai_3_6(self):
        from api.test_retelling import retelling_result
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.seed()
        with patch('api.views.check_retelling_audio', return_value=(
            retelling_result(), {'recognized': 'Москва — красивый город.', 'passing_score': 60},
        )) as check:
            response = self.client.post('/api/retelling/check', {
                'task_id': 'moscow_retelling', 'task_code': 'AI_3_6',
                'student_code': TEST_STUDENT_CODE,
                'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(check.call_args.kwargs['task_id'], 'moscow_retelling')
        attempt = TaskAttempt.objects.get()
        self.assertEqual(attempt.task.code, 'AI_3_6')
        self.assertEqual(attempt.task.lesson.position, 3)

    def test_novgorod_retelling_saves_under_its_own_task(self):
        from api.test_retelling import retelling_result
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.seed()
        for score in (59, 60):
            speech = {'recognized': 'Я студент. Я историк.', 'duration': 20,
                      'passing_score': 60, 'stress_check': {'status': 'not_assessed'}}
            with patch('api.views.check_retelling_audio', return_value=(retelling_result(score), speech)) as check:
                response = self.client.post('/api/retelling/check', {
                    'task_id': 'novgorod_retelling', 'task_code': 'AI_3_11',
                    'student_code': TEST_STUDENT_CODE,
                    'file': SimpleUploadedFile('record.webm', b'audio'),
                })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['saved'])
            self.assertEqual(check.call_args.kwargs['task_id'], 'novgorod_retelling')
        attempts = TaskAttempt.objects.filter(task__code='AI_3_11').order_by('pk')
        self.assertEqual(list(attempts.values_list('score', flat=True)), [59, 60])
        self.assertEqual(list(attempts.values_list('is_completed', flat=True)), [False, True])
