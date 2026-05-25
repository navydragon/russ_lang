from django.contrib import admin
from .models import Group, Student


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Group.
    """
    list_display = ('name', 'code', 'curator', 'get_students_count')
    list_filter = ('curator',)
    search_fields = ('name', 'code', 'curator__username', 'curator__last_name', 'curator__first_name')
    list_editable = ('code',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code')
        }),
        ('Куратор', {
            'fields': ('curator',)
        }),
    )
    
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
