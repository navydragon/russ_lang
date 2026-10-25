import hashlib

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction, DatabaseError

from courses.course_sync import COURSE_NAME, DEFAULT_TASKS_FILE, read_regular_tasks, build_plan, apply_plan
from courses.task_catalog import TASK_CATALOG


class Command(BaseCommand):
    help = 'Идемпотентно создаёт курс, уроки 1–10, задания Excel и AI_Nурока_Nзадания. По умолчанию только план.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Применить план одной транзакцией.')
        parser.add_argument('--tasks-file', default=str(DEFAULT_TASKS_FILE))

    def handle(self, *args, **options):
        regular = read_regular_tasks(options['tasks_file'])
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        if options['apply']:
                            lock_id = int.from_bytes(hashlib.sha256(COURSE_NAME.encode()).digest()[:8], 'big', signed=True)
                            cursor.execute('SET LOCAL lock_timeout = \'10s\'')
                            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [lock_id])
                            # Сериализуем изменения таблиц каталога на время проверки и вставки.
                            cursor.execute('LOCK TABLE courses_course, courses_lesson, courses_task IN SHARE ROW EXCLUSIVE MODE')
                        else:
                            cursor.execute('SET TRANSACTION READ ONLY')
                plan = build_plan(regular)
                self.stdout.write(f'Курс: {COURSE_NAME}')
                self.stdout.write(
                    f'Добавить: курсов {int(plan.course_id is None)}, уроков {len(plan.missing_lessons)}, '
                    f'заданий {len(plan.new_tasks)}; обновить кодов {len(plan.code_updates)}; '
                    f'существующих заданий {plan.existing_tasks}.'
                )
                self.stdout.write(f'Целевой состав: 10 уроков, {len(regular)} обычных + {len(TASK_CATALOG)} ИИ-задания.')
                for number in range(1, 11):
                    ai = [t.code for t in TASK_CATALOG if t.lesson == number]
                    self.stdout.write(f'Урок {number}: обычных {sum(t.lesson == number for t in regular)}, ИИ {len(ai)}' + (f' ({", ".join(ai)})' if ai else ''))
                if options['apply']:
                    course = apply_plan(plan)
                    self.stdout.write(self.style.SUCCESS(f'Применено. ID курса: {course.pk}. Существующие результаты сохранены.'))
                else:
                    self.stdout.write('Только план, изменений в БД нет. Для записи добавьте --apply.')
        except DatabaseError as exc:
            raise CommandError(
                'Не удалось выполнить синхронизацию БД. Изменения транзакции отменены. '
                'Проверьте подключение, схему и права пользователя БД.'
            ) from exc
