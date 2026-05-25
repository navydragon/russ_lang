from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from django.views.generic import TemplateView, UpdateView, ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from .forms import ProfileEditForm, UserForm, UserPasswordChangeForm

User = get_user_model()


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Главная страница профиля пользователя с вкладками.
    """
    template_name = 'users/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        # Инициализируем форму редактирования для отображения на главной странице
        context['form'] = ProfileEditForm(instance=self.request.user)
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования данных профиля.
    """
    template_name = 'users/profile.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('users:profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Данные профиля успешно обновлены.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['active_tab'] = 'edit'
        return context


class ProfilePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    Представление для изменения пароля пользователя.
    """
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменен.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['active_tab'] = 'password'
        return context


class AdminPanelView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Страница-заглушка для администрирования.
    Доступна только для пользователей с is_staff=True.
    """
    template_name = 'users/admin_panel.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class CustomPasswordResetView(PasswordResetView):
    """
    Представление для запроса сброса пароля.
    """
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Если указанный email существует в системе, на него было отправлено письмо с инструкциями по восстановлению пароля.'
        )
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Представление для подтверждения отправки письма со ссылкой для сброса пароля.
    """
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Представление для установки нового пароля.
    """
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.')
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Представление для подтверждения успешного сброса пароля.
    """
    template_name = 'users/password_reset_complete.html'


# ========== CRUD представления для управления пользователями ==========

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Главная страница управления пользователями со списком всех пользователей.
    Доступна только для пользователей с is_staff=True.
    """
    model = User
    template_name = 'users/user_management.html'
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return User.objects.all().order_by('last_name', 'first_name', 'username')


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Представление для создания нового пользователя.
    """
    model = User
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_management')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        # Генерируем случайный пароль для нового пользователя
        password = get_random_string(length=12)
        user = form.save(commit=False)
        user.set_password(password)
        user.save()
        
        messages.success(
            self.request,
            f'Пользователь "{user.username}" успешно создан. Временный пароль: {password}'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание пользователя'
        return context


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Представление для редактирования пользователя.
    """
    model = User
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_management')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, f'Пользователь "{form.instance.username}" успешно обновлен.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование пользователя'
        return context


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Представление для удаления пользователя.
    """
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_management')
    context_object_name = 'user_to_delete'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        user_to_delete = self.get_object()
        current_user = request.user
        
        # Проверяем, что пользователь не пытается удалить самого себя
        if user_to_delete.pk == current_user.pk:
            messages.error(
                request,
                'Вы не можете удалить свой собственный аккаунт.'
            )
            return redirect('users:user_management')
        
        username = user_to_delete.username
        messages.success(request, f'Пользователь "{username}" успешно удален.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Переименовываем для избежания конфликта с request.user
        context['user_to_delete'] = self.get_object()
        return context


class UserPasswordChangeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Представление для смены пароля пользователя администратором.
    """
    template_name = 'users/user_password_change.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, pk=kwargs.get('pk'))
        context['user_to_change'] = user
        
        if self.request.method == 'POST':
            form = UserPasswordChangeForm(user, self.request.POST)
        else:
            form = UserPasswordChangeForm(user)
        
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs.get('pk'))
        form = UserPasswordChangeForm(user, request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Пароль пользователя "{user.username}" успешно изменен.'
            )
            return redirect('users:user_management')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)
