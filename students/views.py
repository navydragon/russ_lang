from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Count
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from .models import Group, Student
from .forms import GroupForm
from . import roster
from .portal import PortalError
from courses.models import Course, Lesson, StudentTask, TaskAttempt


class CustomLoginView(LoginView):
    """
    Представление для авторизации пользователя.
    """
    template_name = 'students/login.html'
    redirect_authenticated_user = True


class MyGroupsView(LoginRequiredMixin, TemplateView):
    """
    Представление для отображения групп пользователя.
    Для обычных пользователей: группы, где пользователь является куратором.
    Для superuser: все группы.
    """
    template_name = 'students/my_groups.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_superuser:
            # Суперпользователь видит все группы
            groups = Group.objects.all().prefetch_related('students', 'curators')
        else:
            # Обычный пользователь видит только свои группы как куратор
            groups = Group.objects.filter(curators=user).prefetch_related('students', 'curators')
        
        context['groups'] = groups
        return context


class CustomLogoutView(LogoutView):
    """
    Представление для выхода из системы.
    """
    pass


class GroupResultsView(LoginRequiredMixin, TemplateView):
    """
    Представление для отображения результатов группы по курсам.
    """
    template_name = 'students/group_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        group_id = kwargs.get('group_id')
        
        # Получаем группу
        group = get_object_or_404(
            Group.objects.prefetch_related('curators'),
            id=group_id
        )
        
        # Проверяем доступ: пользователь должен быть куратором группы или superuser
        if not user.is_superuser and not group.has_curator(user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет доступа к этой группе")
        
        # Получаем все курсы
        courses = Course.objects.all().order_by('name')
        
        # Получаем выбранный курс (из GET параметра или первый по умолчанию)
        course_id = self.request.GET.get('course_id')
        if course_id:
            try:
                selected_course = Course.objects.prefetch_related(
                    Prefetch(
                        'lessons',
                        queryset=Lesson.objects.prefetch_related('tasks').order_by('position', 'name')
                    )
                ).get(id=course_id)
            except Course.DoesNotExist:
                selected_course = None
        else:
            selected_course = None
        
        # Если курс не выбран, берем первый курс с prefetch
        if not selected_course and courses.exists():
            selected_course = Course.objects.prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=Lesson.objects.prefetch_related('tasks').order_by('position', 'name')
                )
            ).first()
        
        # Получаем студентов группы в алфавитном порядке с оптимизацией запросов
        students = group.students.all().order_by('last_name', 'first_name').prefetch_related(
            Prefetch(
                'completed_tasks',
                queryset=StudentTask.objects.select_related('task__lesson').all()
            )
        )
        
        # Подготавливаем данные для таблицы
        results_data = []
        lessons = []
        
        if selected_course:
            # Получаем уроки выбранного курса
            lessons = list(selected_course.lessons.all())
            
            # Для каждого студента создаем список с результатами по урокам (в том же порядке, что и lessons)
            for student in students:
                lesson_results = []
                
                # Для каждого урока подсчитываем завершенные задания
                for lesson in lessons:
                    # Количество завершенных заданий студента в этом уроке
                    completed_count = sum(
                        1 for ct in student.completed_tasks.all()
                        if ct.task.lesson_id == lesson.id
                    )
                    
                    # Общее количество заданий в уроке (используем prefetched данные)
                    total_tasks = len(lesson.tasks.all())
                    
                    lesson_results.append({
                        'lesson_id': lesson.id,
                        'completed': completed_count,
                        'total': total_tasks
                    })
                
                results_data.append({
                    'student': student,
                    'lesson_results': lesson_results
                })
        
        context['group'] = group
        context['courses'] = courses
        context['selected_course'] = selected_course
        context['lessons'] = lessons
        context['results_data'] = results_data
        
        return context


class StudentLessonResultsView(LoginRequiredMixin, TemplateView):
    """
    Представление для отображения детальных результатов урока студента.
    """
    template_name = 'students/student_lesson_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        student_id = kwargs.get('student_id')
        lesson_id = kwargs.get('lesson_id')
        
        # Получаем студента с оптимизацией запросов
        student = get_object_or_404(
            Student.objects.select_related('group').prefetch_related('group__curators'),
            id=student_id
        )
        
        # Проверяем доступ: пользователь должен быть куратором группы студента или superuser
        if not user.is_superuser and (not student.group or not student.group.has_curator(user)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет доступа к результатам этого студента")
        
        # Получаем урок с оптимизацией запросов
        lesson = get_object_or_404(
            Lesson.objects.select_related('course').prefetch_related('tasks'),
            id=lesson_id
        )
        
        # Получаем все задания урока с попытками студента (оптимизация для избежания N+1)
        # Вариант 1: Получаем все попытки одним запросом и группируем по заданиям
        all_attempts = TaskAttempt.objects.filter(
            student=student,
            task__lesson=lesson
        ).select_related('task').order_by('task__position', 'datetime')
        
        # Группируем попытки по заданиям
        attempts_by_task = {}
        for attempt in all_attempts:
            task_id = attempt.task_id
            if task_id not in attempts_by_task:
                attempts_by_task[task_id] = []
            attempts_by_task[task_id].append(attempt)
        
        # Получаем задания урока и добавляем попытки
        tasks_data = []
        for task in lesson.tasks.all().order_by('position', 'name'):
            attempts = attempts_by_task.get(task.id, [])
            # Нумеруем попытки по порядку (1, 2, 3...)
            numbered_attempts = []
            for idx, attempt in enumerate(attempts, start=1):
                numbered_attempts.append({
                    'number': idx,
                    'attempt': attempt
                })
            
            tasks_data.append({
                'task': task,
                'attempts': numbered_attempts
            })
        
        context['student'] = student
        context['lesson'] = lesson
        context['group'] = student.group
        context['tasks_data'] = tasks_data
        
        return context


@login_required
def index(request):
    """
    Главная страница - редирект на страницу групп.
    """
    return redirect('students:my_groups')


# ========== CRUD представления для управления группами ==========

class GroupManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Главная страница управления группами со списком всех групп.
    Доступна только для пользователей с is_staff=True.
    """
    model = Group
    template_name = 'students/group_management.html'
    context_object_name = 'groups'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return Group.objects.annotate(
            students_count=Count('students')
        ).prefetch_related('curators', 'courses').order_by('name')


class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Представление для создания новой группы.
    """
    model = Group
    form_class = GroupForm
    template_name = 'students/group_form.html'
    success_url = reverse_lazy('students:group_management')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        try:
            self.object = roster.save_group(form)
        except PortalError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, 'Группа успешно создана.')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание группы'
        return context


class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Представление для редактирования группы.
    """
    model = Group
    form_class = GroupForm
    template_name = 'students/group_form.html'
    success_url = reverse_lazy('students:group_management')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        try:
            self.object = roster.save_group(form)
        except PortalError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, 'Группа успешно обновлена.')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование группы'
        return context


class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Представление для удаления группы.
    """
    model = Group
    template_name = 'students/group_confirm_delete.html'
    success_url = reverse_lazy('students:group_management')
    context_object_name = 'group'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return Group.objects.annotate(
            students_count=Count('students')
        )

    def form_valid(self, form):
        try:
            roster.delete_group(self.object.pk)
        except PortalError as exc:
            messages.error(self.request, str(exc))
        else:
            messages.success(self.request, 'Группа удалена.')
        return redirect(self.success_url)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.form_valid(self.get_form())


class GroupStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Представление для просмотра списка студентов группы и управления ими.
    """
    template_name = 'students/group_students.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = kwargs.get('group_id')
        group = get_object_or_404(Group.objects.prefetch_related('courses'), id=group_id)
        
        students = group.students.all().order_by('last_name', 'first_name', 'middle_name')
        
        context['group'] = group
        context['students'] = students
        return context


class RemoveStudentFromGroupView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Представление для удаления студента из группы (установка group=None).
    """
    model = Student
    template_name = 'students/student_remove_confirm.html'
    context_object_name = 'student'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_object(self, queryset=None):
        student = get_object_or_404(Student, id=self.kwargs.get('student_id'))
        return student
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(Group.objects.prefetch_related('courses'), id=group_id)
        context['group'] = group
        return context
    
    def get_success_url(self):
        group_id = self.kwargs.get('group_id')
        return reverse_lazy('students:group_students', kwargs={'group_id': group_id})

    def form_valid(self, form):
        try:
            roster.remove_student(self.kwargs['group_id'], self.object.pk)
        except PortalError as exc:
            messages.error(self.request, str(exc))
        else:
            messages.success(self.request, 'Студент исключён из группы. Пользователь и результаты сохранены.')
        return redirect(self.get_success_url())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.form_valid(self.get_form())
