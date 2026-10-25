from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.models import Course, Lesson, Task
from courses.task_catalog import (
    TASK_CATALOG, TEST_COURSE_NAME, TEST_GROUP_CODE, TEST_STUDENT_CODE,
)
from students.models import Group, Student


class Command(BaseCommand):
    help = 'Создаёт локальный тестовый курс, 4 урока, 31 задание и тестового ученика.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Тестовые данные создаются только при DEBUG=True.')

        # Поддерживаем прежний локальный набор, сохраняя id заданий и попытки.
        for definition in TASK_CATALOG:
            legacy = Task.objects.filter(
                code=definition.legacy_code,
                lesson__course__name=TEST_COURSE_NAME,
                lesson__position=definition.lesson, position=definition.position,
            )
            if legacy.count() > 1:
                raise CommandError(f'Найдены дубли {definition.legacy_code}.')
            if legacy.exists():
                if Task.objects.filter(code=definition.code).exists():
                    raise CommandError(f'Новый код {definition.code} уже занят.')
                legacy.update(code=definition.code)

        # Не переиспользуем задания другого курса и не меняем реальные записи.
        for definition in TASK_CATALOG:
            matches = Task.objects.filter(code=definition.code)
            if matches.count() > 1 or matches.exclude(
                lesson__course__name=TEST_COURSE_NAME,
                lesson__position=definition.lesson,
                position=definition.position,
            ).exists():
                raise CommandError(f'Код {definition.code} уже занят другим заданием.')

        group, _ = Group.objects.get_or_create(
            code=TEST_GROUP_CODE, defaults={'name': 'Тестовая группа ИИ'},
        )
        student, created_student = Student.objects.get_or_create(
            code=TEST_STUDENT_CODE,
            defaults={'last_name': 'Тестовый', 'first_name': 'Ученик', 'group': group},
        )
        if not created_student and (
            student.group_id != group.pk
            or student.last_name != 'Тестовый'
            or student.first_name != 'Ученик'
        ):
            raise CommandError('Код тестового ученика уже занят другой записью.')

        course, _ = Course.objects.get_or_create(name=TEST_COURSE_NAME)
        lessons = {}
        for position in range(1, 5):
            lessons[position], _ = Lesson.objects.get_or_create(
                course=course, position=position,
                defaults={'name': f'Урок {position}'},
            )
        created_count = 0
        for definition in TASK_CATALOG:
            lesson = lessons[definition.lesson]
            if Task.objects.filter(lesson=lesson, position=definition.position).exclude(
                code=definition.code,
            ).exists():
                raise CommandError(
                    f'Урок {definition.lesson}, позиция {definition.position} уже занята.'
                )
            _, created = Task.objects.get_or_create(
                code=definition.code,
                defaults={
                    'name': definition.name, 'lesson': lesson,
                    'position': definition.position,
                },
            )
            created_count += int(created)

        self.stdout.write(self.style.SUCCESS(
            f'Готово: 4 урока, {len(TASK_CATALOG)} заданий '
            f'(новых: {created_count}), student_code={student.code}. '
            'Существующие попытки сохранены.'
        ))
        self.stdout.write('Страница запуска: /dev/tasks/')
