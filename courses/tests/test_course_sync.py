from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from courses.course_sync import COURSE_NAME, DEFAULT_TASKS_FILE, read_regular_tasks
from courses.models import Course, Lesson, Task, TaskAttempt, StudentTask
from courses.task_catalog import TASK_CATALOG
from students.models import Student


class CourseSyncTests(TestCase):
    def run_sync(self, apply=False):
        output = StringIO()
        call_command('sync_russian_course', apply=apply, stdout=output)
        return output.getvalue()

    def test_default_is_read_only(self):
        output = self.run_sync()
        self.assertIn('изменений в БД нет', output)
        self.assertEqual(Course.objects.count(), 0)
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)

    def test_two_runs_preserve_existing_records_and_results(self):
        course = Course.objects.create(name=COURSE_NAME)
        lesson = Lesson.objects.create(course=course, name='Первый урок', position=1)
        task = Task.objects.create(lesson=lesson, code='teacher_task', name='Своя работа', position=55)
        student = Student.objects.create(code='existing', first_name='Тест', last_name='Тест')
        attempt = TaskAttempt.objects.create(student=student, task=task, datetime=timezone.now(), score=87)
        completion = StudentTask.objects.create(student=student, task=task, completion_date=timezone.now().date(), completion_attempt=1)
        self.run_sync(apply=True)
        snapshot = list(Task.objects.order_by('pk').values_list('pk', 'code', 'position'))
        output = self.run_sync(apply=True)
        self.assertIn('заданий 0; обновить кодов 0', output)
        self.assertEqual(snapshot, list(Task.objects.order_by('pk').values_list('pk', 'code', 'position')))
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Lesson.objects.count(), 10)
        self.assertEqual(Task.objects.count(), len(read_regular_tasks(DEFAULT_TASKS_FILE)) + 31 + 1)
        self.assertTrue(TaskAttempt.objects.filter(pk=attempt.pk, score=87).exists())
        self.assertTrue(StudentTask.objects.filter(pk=completion.pk).exists())
        lesson.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(lesson.name, 'Первый урок')
        self.assertEqual(task.position, 55)

    def test_lesson_positions_are_used_instead_of_database_ids(self):
        course = Course.objects.create(pk=78, name=COURSE_NAME)
        lesson = Lesson.objects.create(pk=300, course=course, position=3, name='Урок 3')
        self.run_sync(apply=True)
        self.assertEqual(Task.objects.get(code='AI_3_1').lesson_id, lesson.pk)
        for task in Task.objects.filter(code__startswith='task').select_related('lesson'):
            self.assertEqual(task.lesson.position, int(task.code.split('-')[0][4:]))

    def test_legacy_ai_code_is_updated_without_losing_attempt(self):
        course = Course.objects.create(name=COURSE_NAME)
        lesson = Lesson.objects.create(course=course, name='Урок 1', position=1)
        task = Task.objects.create(lesson=lesson, code='family_story', name='Семья', position=1)
        student = Student.objects.create(code='legacy', first_name='Тест', last_name='Тест')
        attempt = TaskAttempt.objects.create(student=student, task=task, datetime=timezone.now())
        self.run_sync(apply=True)
        task.refresh_from_db()
        self.assertEqual(task.code, 'AI_1_1')
        self.assertEqual(attempt.task_id, task.pk)
        self.assertEqual(TaskAttempt.objects.get(pk=attempt.pk).task.code, 'AI_1_1')

    def test_code_conflict_rolls_back_without_changing_other_course(self):
        other = Course.objects.create(name='Другой курс')
        lesson = Lesson.objects.create(course=other, name='Урок 1', position=1)
        task = Task.objects.create(lesson=lesson, code='AI_1_1', position=1, name='Занятый код')
        with self.assertRaises(CommandError):
            self.run_sync(apply=True)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Task.objects.get(pk=task.pk).name, 'Занятый код')

    def test_catalog_codes_are_unique_and_sequential_per_lesson(self):
        self.assertEqual(len({d.code for d in TASK_CATALOG}), 31)
        for lesson in range(1, 11):
            definitions = [d for d in TASK_CATALOG if d.lesson == lesson]
            self.assertEqual([d.code for d in definitions], [f'AI_{lesson}_{n}' for n in range(1, max((d.position for d in definitions), default=0) + 1) if f'AI_{lesson}_{n}' != 'AI_3_3'])

    def test_duplicate_cleanup_is_repeatable_and_sync_does_not_recreate_it(self):
        self.run_sync(apply=True)
        lesson = Lesson.objects.get(course__name=COURSE_NAME, position=3)
        task = Task.objects.create(lesson=lesson, position=100, code='AI_3_3', name='Вопросы и пересказ «Наш университет»')
        call_command('remove_duplicate_ai_task', stdout=StringIO())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        call_command('remove_duplicate_ai_task', apply=True, stdout=StringIO())
        call_command('remove_duplicate_ai_task', apply=True, stdout=StringIO())
        self.run_sync(apply=True)
        self.assertFalse(Task.objects.filter(code='AI_3_3').exists())

    def test_duplicate_cleanup_preserves_task_with_results(self):
        course = Course.objects.create(name=COURSE_NAME)
        lesson = Lesson.objects.create(course=course, position=3, name='Урок 3')
        task = Task.objects.create(lesson=lesson, position=1, code='AI_3_3', name='Вопросы и пересказ «Наш университет»')
        student = Student.objects.create(code='protected', first_name='Тест', last_name='Тест')
        TaskAttempt.objects.create(student=student, task=task, datetime=timezone.now())
        with self.assertRaises(CommandError):
            call_command('remove_duplicate_ai_task', apply=True, stdout=StringIO())
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
