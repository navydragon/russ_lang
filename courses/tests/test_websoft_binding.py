from io import StringIO

from django import forms
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from courses.course_sync import COURSE_NAME
from courses.models import Course
from courses.task_catalog import TEST_COURSE_NAME
from courses.websoft import RUSSIAN_COURSE_WEBSOFT_ID


class CourseBindingTests(TestCase):
    def sync(self):
        call_command('sync_russian_course', apply=True, stdout=StringIO())

    def test_sync_assigns_id_and_repeat_preserves_course(self):
        course = Course.objects.create(name=COURSE_NAME)
        self.sync()
        self.sync()
        course.refresh_from_db()
        self.assertEqual(course.websoft_id, RUSSIAN_COURSE_WEBSOFT_ID)
        self.assertEqual(Course.objects.count(), 1)

    def test_sync_creates_bound_course(self):
        self.sync()
        self.assertEqual(Course.objects.get(name=COURSE_NAME).websoft_id, RUSSIAN_COURSE_WEBSOFT_ID)

    def test_sync_rejects_conflicting_binding(self):
        Course.objects.create(name=COURSE_NAME, websoft_id='123')
        with self.assertRaises(CommandError):
            self.sync()
        self.assertEqual(Course.objects.get().websoft_id, '123')

    def test_sync_rejects_other_course_with_same_id_or_duplicate_name(self):
        Course.objects.create(name='Другой', websoft_id=RUSSIAN_COURSE_WEBSOFT_ID)
        with self.assertRaises(CommandError):
            self.sync()
        Course.objects.all().delete()
        Course.objects.bulk_create([Course(name=COURSE_NAME), Course(name=COURSE_NAME)])
        with self.assertRaises(CommandError):
            self.sync()

    def test_test_seed_does_not_assign_production_id(self):
        with self.settings(DEBUG=True):
            call_command('seed_ai_test_data', stdout=StringIO())
        self.assertIsNone(Course.objects.get(name=TEST_COURSE_NAME).websoft_id)

    def test_id_validation_empty_normalization_and_form(self):
        class CourseForm(forms.ModelForm):
            class Meta:
                model = Course
                fields = ['name', 'websoft_id']
        for invalid in ('0', '-1', '12.5', '001', '9223372036854775808', '١٢٣'):
            form = CourseForm({'name': 'Курс', 'websoft_id': invalid})
            self.assertFalse(form.is_valid(), invalid)
        course = Course.objects.create(name='Пустой', websoft_id='')
        self.assertIsNone(Course.objects.get(pk=course.pk).websoft_id)
        self.assertIsNone(Course.objects.create(name='Пробелы', websoft_id='   ').websoft_id)
        form = CourseForm({'name': 'Связанный', 'websoft_id': RUSSIAN_COURSE_WEBSOFT_ID})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().websoft_id, RUSSIAN_COURSE_WEBSOFT_ID)
        self.assertFalse(CourseForm({'name': 'Дубль', 'websoft_id': RUSSIAN_COURSE_WEBSOFT_ID}).is_valid())


class BindingMigrationTests(TransactionTestCase):
    def test_existing_relations_and_results_survive_and_groups_stay_unassigned(self):
        executor = MigrationExecutor(connection)
        before = [('courses', '0001_initial'), ('students', '0006_portal_roster')]
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        course = apps.get_model('courses', 'Course').objects.create(name=COURSE_NAME)
        lesson = apps.get_model('courses', 'Lesson').objects.create(name='Урок', course_id=course.pk)
        task = apps.get_model('courses', 'Task').objects.create(name='Задание', lesson_id=lesson.pk)
        group = apps.get_model('students', 'Group').objects.create(name='Группа', code='migration')
        student = apps.get_model('students', 'Student').objects.create(code='migration', first_name='Имя', last_name='Фамилия', group_id=group.pk)
        attempt = apps.get_model('courses', 'TaskAttempt').objects.create(student_id=student.pk, task_id=task.pk, datetime=timezone.now(), results='saved')
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
            from students.models import Group
            from courses.models import Lesson, TaskAttempt
            self.assertEqual(Course.objects.get(pk=course.pk).websoft_id, RUSSIAN_COURSE_WEBSOFT_ID)
            self.assertEqual(Lesson.objects.get(pk=lesson.pk).course_id, course.pk)
            self.assertEqual(TaskAttempt.objects.get(pk=attempt.pk).results, 'saved')
            self.assertFalse(Group.objects.get(pk=group.pk).courses.exists())
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
