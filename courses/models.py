from django.db import models
from students.models import Student


class Course(models.Model):
    """
    Модель курса.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        db_table = 'courses_course'
        ordering = ['name']

    def __str__(self):
        return self.name


class Lesson(models.Model):
    """
    Модель урока.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс',
        related_name='lessons'
    )
    position = models.PositiveIntegerField(
        default=0,
        verbose_name='Позиция'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        db_table = 'courses_lesson'
        ordering = ['course', 'position', 'name']
        unique_together = [['course', 'position']]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Task(models.Model):
    """
    Модель задания.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    code = models.CharField(
        max_length=100,
        verbose_name='Код',
        blank=True
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name='Урок',
        related_name='tasks'
    )
    position = models.PositiveIntegerField(
        default=0,
        verbose_name='Позиция'
    )

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        db_table = 'courses_task'
        ordering = ['lesson', 'position', 'name']
        unique_together = [['lesson', 'position']]

    def __str__(self):
        return f"{self.lesson.name} - {self.name}"


class StudentTask(models.Model):
    """
    Модель задания студента (завершенное задание).
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        verbose_name='Студент',
        related_name='completed_tasks'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name='Задание',
        related_name='student_completions'
    )
    completion_date = models.DateField(
        verbose_name='Дата завершения'
    )
    completion_attempt = models.PositiveIntegerField(
        verbose_name='Номер попытки завершения'
    )

    class Meta:
        verbose_name = 'Задание студента'
        verbose_name_plural = 'Задания студентов'
        db_table = 'courses_student_task'
        unique_together = [['student', 'task']]
        ordering = ['-completion_date', 'student']

    def __str__(self):
        return f"{self.student} - {self.task}"


class TaskAttempt(models.Model):
    """
    Модель попытки выполнения задания.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        verbose_name='Студент',
        related_name='task_attempts'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name='Задание',
        related_name='attempts'
    )
    datetime = models.DateTimeField(
        verbose_name='Дата и время попытки'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Успешна ли попытка'
    )
    score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Баллы'
    )
    score_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Баллы (%)'
    )
    results = models.TextField(
        blank=True,
        verbose_name='Подробный результат'
    )

    class Meta:
        verbose_name = 'Попытка выполнения задания'
        verbose_name_plural = 'Попытки выполнения заданий'
        db_table = 'courses_task_attempt'
        ordering = ['-datetime', 'student']

    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{self.student} - {self.task} [{status}] {self.datetime.strftime('%Y-%m-%d %H:%M')}"
