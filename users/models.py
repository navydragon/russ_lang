from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Кастомная модель пользователя с дополнительными полями:
    - Фамилия (last_name)
    - Имя (first_name)
    - Отчество (middle_name)
    """
    # Переопределяем поля для русских названий
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        blank=True
    )
    # Добавляем Отчество
    middle_name = models.CharField(
        max_length=150,
        verbose_name='Отчество',
        blank=True,
        null=True
    )
    is_tutor = models.BooleanField(
        default=False,
        verbose_name='Куратор',
        help_text='Определяет, может ли пользователь быть назначен куратором группы'
    )
    # Флаг для отправки писем куратору
    send_emails = models.BooleanField(
        default=False,
        verbose_name='Отправлять письма',
        help_text='Если включено, куратор будет получать пересылаемые письма от студентов своей группы'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users_user'

    def __str__(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(filter(None, parts)) or self.username
