from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.course_sync import COURSE_NAME
from courses.models import Task, TaskAttempt, StudentTask
from courses.task_catalog import TEST_COURSE_NAME


class Command(BaseCommand):
    help = 'Удаляет только пустую заглушку AI_3_3, дублирующую AI_3_2. Без --apply только проверка.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        query = Task.objects.filter(
            code='AI_3_3', lesson__course__name__in=[COURSE_NAME, TEST_COURSE_NAME],
        )
        if options['apply']:
            query = query.select_for_update()
        tasks = list(query)
        if any(t.lesson.position != 3 or t.name != 'Вопросы и пересказ «Наш университет»' for t in tasks):
            raise CommandError('Запись AI_3_3 отличается от удаляемого дубля; удаление отменено.')
        if TaskAttempt.objects.filter(task__in=tasks).exists() or StudentTask.objects.filter(task__in=tasks).exists():
            raise CommandError('У AI_3_3 есть результаты; удаление отменено, чтобы сохранить данные.')
        self.stdout.write(f'Пустых заглушок AI_3_3: {len(tasks)}. Результатов нет.')
        if options['apply']:
            for task in tasks:
                task.delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено заглушок: {len(tasks)}. Другие задания не изменены.'))
        else:
            self.stdout.write('Только проверка; для удаления добавьте --apply.')
