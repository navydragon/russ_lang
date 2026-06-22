from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админ-интерфейс для кастомной модели пользователя.
    """
    list_display = ('username', 'email', 'last_name', 'first_name', 'middle_name', 'is_staff', 'is_tutor', 'is_active')
    list_filter = ('is_staff', 'is_tutor', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'middle_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('last_name', 'first_name', 'middle_name', 'email')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_tutor', 'groups', 'user_permissions'),
        }),
        ('Дополнительно', {'fields': ('send_emails',)}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Личная информация', {
            'fields': ('last_name', 'first_name', 'middle_name', 'email'),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_tutor'),
        }),
        ('Дополнительно', {
            'fields': ('send_emails',),
        }),
    )
