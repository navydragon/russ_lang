from django.contrib import admin
from .models import Course, Lesson, Task, StudentTask, TaskAttempt


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Course.
    """
    list_display = ('name', 'get_lessons_count')
    search_fields = ('name',)
    
    def get_lessons_count(self, obj):
        """Возвращает количество уроков в курсе."""
        return obj.lessons.count()
    get_lessons_count.short_description = 'Количество уроков'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Lesson.
    """
    list_display = ('name', 'course', 'position', 'get_tasks_count')
    list_filter = ('course',)
    search_fields = ('name', 'course__name')
    list_editable = ('position',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'course', 'position')
        }),
    )
    
    def get_tasks_count(self, obj):
        """Возвращает количество заданий в уроке."""
        return obj.tasks.count()
    get_tasks_count.short_description = 'Количество заданий'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Task.
    """
    list_display = ('name', 'code', 'lesson', 'position', 'get_attempts_count', 'get_completions_count')
    list_filter = ('lesson__course', 'lesson')
    search_fields = ('name', 'code', 'lesson__name', 'lesson__course__name')
    list_editable = ('position',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'lesson', 'position')
        }),
    )
    
    def get_attempts_count(self, obj):
        """Возвращает количество попыток выполнения задания."""
        return obj.attempts.count()
    get_attempts_count.short_description = 'Попыток'
    
    def get_completions_count(self, obj):
        """Возвращает количество завершенных заданий."""
        return obj.student_completions.count()
    get_completions_count.short_description = 'Завершено'


@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели StudentTask.
    """
    list_display = ('student', 'task', 'completion_date', 'completion_attempt')
    list_filter = ('completion_date', 'task__lesson__course', 'task__lesson')
    search_fields = (
        'student__last_name', 
        'student__first_name', 
        'student__code',
        'task__name',
        'task__lesson__name',
        'task__lesson__course__name'
    )
    
    fieldsets = (
        ('Связи', {
            'fields': ('student', 'task')
        }),
        ('Информация о завершении', {
            'fields': ('completion_date', 'completion_attempt')
        }),
    )


@admin.register(TaskAttempt)
class TaskAttemptAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели TaskAttempt.
    """
    list_display = ('student', 'task', 'datetime', 'is_completed', 'score', 'score_percent')
    list_filter = ('is_completed', 'datetime', 'task__lesson__course', 'task__lesson')
    search_fields = (
        'student__last_name',
        'student__first_name',
        'student__code',
        'task__name',
        'task__code',
        'task__lesson__name',
        'task__lesson__course__name'
    )
    readonly_fields = ('datetime',)
    date_hierarchy = 'datetime'
    
    fieldsets = (
        ('Связи', {
            'fields': ('student', 'task')
        }),
        ('Результаты попытки', {
            'fields': ('datetime', 'is_completed', 'score', 'score_percent', 'results')
        }),
    )
