from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Group, Student

User = get_user_model()


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Group.
    """
    list_display = ('name', 'code', 'get_curators_display', 'get_students_count')
    list_filter = ('curators',)
    search_fields = ('name', 'code', 'curators__username', 'curators__last_name', 'curators__first_name')
    list_editable = ('code',)
    filter_horizontal = ('curators',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code')
        }),
        ('Кураторы', {
            'fields': ('curators',)
        }),
    )

    def get_curators_display(self, obj):
        """Возвращает список кураторов через запятую."""
        return ', '.join(
            c.get_full_name() or c.username for c in obj.curators.all()
        ) or '—'
    get_curators_display.short_description = 'Кураторы'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'curators':
            kwargs['queryset'] = User.objects.filter(is_tutor=True).order_by('last_name', 'first_name', 'username')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_students_count(self, obj):
        """Возвращает количество студентов в группе."""
        return obj.students.count()
    get_students_count.short_description = 'Количество студентов'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Student.
    """
    list_display = ('last_name', 'first_name', 'middle_name', 'code', 'group')
    list_filter = ('group',)
    search_fields = ('last_name', 'first_name', 'middle_name', 'code', 'group__name', 'group__code')
    list_editable = ('group',)

    fieldsets = (
        ('Личные данные', {
            'fields': ('last_name', 'first_name', 'middle_name')
        }),
        ('Учебная информация', {
            'fields': ('code', 'group')
        }),
    )
