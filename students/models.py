from django.db import models
from django.conf import settings


class Group(models.Model):
    """
    Модель группы студентов.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код'
    )
    curator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Куратор',
        related_name='curated_groups'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        db_table = 'students_group'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Student(models.Model):
    """
    Модель студента.
    """
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    middle_name = models.CharField(
        max_length=150,
        verbose_name='Отчество',
        blank=True,
        null=True
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код'
    )
    sid = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID во внешней системе',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Группа',
        related_name='students'
    )

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        db_table = 'students_student'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(filter(None, parts)) or self.code
