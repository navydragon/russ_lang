import re
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


def _page_scripts(page, html):
    parser = _TaskAssetParser()
    parser.feed(html)
    sources = [html]
    for reference in parser.references:
        parsed = urlsplit(reference)
        if parsed.scheme or reference.startswith(('/', '#', 'data:')) or not parsed.path.endswith('.js'):
            continue
        script = (page.parent / unquote(parsed.path)).resolve()
        if script.is_file():
            sources.append(script.read_text(encoding='utf-8'))
    return '\n'.join(sources)


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
        self.assertEqual(Lesson.objects.count(), 10)
        self.assertEqual(Task.objects.count(), len(TASK_CATALOG))
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
        self.assertContains(response, 'Открыть задание', count=sum(bool(item.html_path) for item in TASK_CATALOG))
        for definition in TASK_CATALOG:
            if definition.html_path:
                self.assertContains(response, '/tasks/' + definition.html_path)
                page = self.client.get('/tasks/' + definition.html_path)
                self.assertEqual(page.status_code, 200)
                page.close()
                source = (Path(settings.BASE_DIR) / 'tasks' / definition.html_path).read_text(encoding='utf-8')
                scripts = _page_scripts(Path(settings.BASE_DIR) / 'tasks' / definition.html_path, source)
                self.assertRegex(scripts, rf'TASK_CODE\s*=\s*[\"\']{re.escape(definition.code)}[\"\']')
                self.assertRegex(scripts, r'API\s*=\s*window\.ANALYZER_CONFIG\.apiBaseUrl')

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
                scripts = _page_scripts(page, html)
                self.assertRegex(scripts, r'API\s*=\s*window\.ANALYZER_CONFIG\.apiBaseUrl')
                self.assertRegex(scripts, rf'TASK_CODE\s*=\s*[\"\']{re.escape(definition.code)}[\"\']')
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

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.story_llm._get_rubric_writing_agent')
    def test_lesson6_university_story_returns_rubric_and_saves_under_ai_6_6(self, get_agent):
        from api.story_llm import WritingRubric

        self.seed()
        grader = get_agent.return_value.run_sync
        grader.return_value.output = WritingRubric(
            content=60, content_reason='Раскрыты все четыре пункта.',
            coherence=25, coherence_reason='Рассказ связный.',
            literacy=15, literacy_reason='Ошибок нет.',
        )
        body = {
            'task_id': 'lesson6_university_story',
            'task_code': 'AI_3_4',
            'student_code': TEST_STUDENT_CODE,
            'text': 'Я учусь в МГУ в Москве, где есть лаборатории и где учатся студенты из разных стран.',
        }
        response = self.client.post('/api/story/check', body, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        grader.assert_not_called()

        body['task_code'] = 'AI_6_6'
        response = self.client.post('/api/story/check', body, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['saved'])
        self.assertEqual(result['score'], 100)
        self.assertEqual(result['rubric']['content'], 60)
        self.assertFalse(result['sentence_limit_applied'])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_6', score=100).exists())

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.story_llm._get_rubric_writing_agent')
    def test_hometown_story_uses_three_part_rubric_and_saves_under_ai_6_11(self, get_agent):
        from api.story_llm import WritingRubric

        self.seed()
        grader = get_agent.return_value.run_sync
        grader.return_value.output = WritingRubric(
            content=60, content_reason='Раскрыты все три пункта.',
            coherence=25, coherence_reason='Рассказ связный.',
            literacy=15, literacy_reason='Ошибок нет.',
        )
        response = self.client.post('/api/story/check', {
            'task_id': 'lesson6_hometown_story', 'task_code': 'AI_6_11',
            'student_code': TEST_STUDENT_CODE,
            'text': 'Мой родной город — Казань. В центре есть пешеходная улица. Символ города — Кремль, '
                    'его знают по белым стенам. Там туристы могут погулять и увидеть старинные здания.',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(response.json()['score'], 100)
        self.assertIn('по 20 за каждый из трёх пунктов', grader.call_args.args[0])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_11', score=100).exists())

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.story_llm._get_rubric_writing_agent')
    def test_shop_dialogue_and_recap_save_under_ai_6_13(self, get_agent):
        from api.story_llm import WritingRubric

        self.seed()
        grader = get_agent.return_value.run_sync
        grader.return_value.output = WritingRubric(
            content=60, content_reason='Есть диалог и краткий пересказ.',
            coherence=25, coherence_reason='Реплики связаны.',
            literacy=15, literacy_reason='Ошибок нет.',
        )
        response = self.client.post('/api/story/check', {
            'task_id': 'lesson6_shop_dialogue', 'task_code': 'AI_6_13',
            'student_code': TEST_STUDENT_CODE,
            'text': 'Саманта: Здравствуйте! Дайте, пожалуйста, две бутылки молока. Сколько с меня?\n'
                    'Продавец: С вас 160 рублей.\nСаманта: Вот 160 рублей. Спасибо!\n\n'
                    'Саманта купила две бутылки молока и заплатила за них 160 рублей.',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(response.json()['score'], 100)
        self.assertIn('до 15 за отдельный пересказ', grader.call_args.args[0])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_13', score=100).exists())

    @override_settings(LLM_API_KEY='test-key')
    @patch('api.story_llm._get_about_me_agent')
    def test_socrates_retelling_uses_its_source_and_saves_under_ai_6_14(self, get_agent):
        from api.story_llm import StoryCheckResult

        self.seed()
        lesson = Lesson.objects.get(course__name=TEST_COURSE_NAME, position=6)
        Task.objects.get_or_create(
            lesson=lesson, position=14,
            defaults={'name': 'Изложение «История о Сократе»', 'code': 'AI_6_14'},
        )
        grader = get_agent.return_value.run_sync
        text = 'Сократ гулял. Прохожий спросил его адрес. Потом он узнал, с кем говорил.'
        grader.return_value.output = StoryCheckResult(
            score=75, ok=True, normalized=text, feedback='Главные события переданы.',
            quality_notes='Можно подробнее рассказать о встрече у дома.',
        )
        response = self.client.post('/api/story/check', {
            'task_id': 'lesson6_socrates_retelling', 'task_code': 'AI_6_14',
            'student_code': TEST_STUDENT_CODE, 'text': text,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertIn('Сократ живёт на этой улице, в доме номер один.', grader.call_args.args[0])
        self.assertTrue(TaskAttempt.objects.filter(task__code='AI_6_14', score=75).exists())

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


class AssignmentReviewConfirmationTests(TestCase):
    @override_settings(DEBUG=True)
    def test_author_review_shows_all_lesson_five_tasks_in_order(self):
        response = self.client.get('/authors/assignments/')
        self.assertEqual(response.status_code, 200)
        lesson = next(item for item in response.context['lessons'] if item['number'] == 5)
        self.assertEqual(
            [row['definition'].code for row in lesson['tasks']],
            [f'AI_5_{position}' for position in range(1, 17)],
        )
        self.assertEqual(lesson['planned'], [])
        for row in lesson['tasks'][9:]:
            definition = row['definition']
            with self.subTest(task=definition.code):
                self.assertIn(definition.code, row['details'])
                self.assertIsNotNone(row['change_date'])
                self.assertContains(response, '/tasks/' + definition.html_path)
                page = self.client.get('/tasks/' + definition.html_path)
                self.assertEqual(page.status_code, 200)
                page.close()

    @override_settings(DEBUG=True)
    def test_confirmation_shared_persistent_and_reversible(self):
        from django.test import Client
        first, second = Client(), Client()
        url = '/dev/tasks/confirmation/'
        self.assertEqual(first.post(url, {'task_code': 'AI_1_4', 'confirmed': 'true'}).status_code, 200)
        self.assertEqual(first.post(url, {'task_code': 'AI_1_4', 'confirmed': 'true'}).status_code, 200)
        response = second.get('/dev/tasks/')
        self.assertContains(response, 'Внесены правки · 10.11.2026')
        self.assertContains(response, 'name="confirmed" checked')
        self.assertEqual(second.post(url, {'task_code': 'AI_1_4', 'confirmed': 'false'}).status_code, 200)
        self.assertNotContains(first.get('/dev/tasks/'), 'name="confirmed" checked')
        self.assertEqual(first.post(url, {'task_code': 'unknown', 'confirmed': 'true'}).status_code, 400)

    @override_settings(DEBUG=False)
    def test_confirmation_disabled_without_debug(self):
        self.assertEqual(self.client.post('/dev/tasks/confirmation/', {'task_code': 'AI_1_4', 'confirmed': 'true'}).status_code, 404)
