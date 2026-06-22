from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AdminPasswordChangeForm

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    """
    Форма для редактирования данных профиля пользователя.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'middle_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email'
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'email': 'Email',
        }


class UserForm(forms.ModelForm):
    """
    Форма для создания и редактирования пользователя администратором.
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'middle_name', 'is_staff', 'is_tutor', 'is_active', 'send_emails']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_tutor': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'send_emails': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'is_staff': 'Персонал',
            'is_tutor': 'Куратор',
            'is_active': 'Активен',
            'send_emails': 'Отправлять письма',
        }
        help_texts = {
            'username': 'Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_',
            'email': 'Email адрес пользователя',
            'is_staff': 'Определяет, может ли пользователь войти в административную панель',
            'is_tutor': 'Определяет, может ли пользователь быть назначен куратором группы',
            'is_active': 'Определяет, считается ли этот пользователь активным. Снимите флажок вместо удаления учетной записи',
            'send_emails': 'Если включено, куратор будет получать пересылаемые письма от студентов своей группы',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Проверка уникальности username (исключая текущий объект при редактировании)
            qs = User.objects.filter(username=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Пользователь с таким именем уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверка уникальности email (исключая текущий объект при редактировании)
            qs = User.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class UserPasswordChangeForm(AdminPasswordChangeForm):
    """
    Форма для смены пароля пользователя администратором.
    Использует встроенную форму Django AdminPasswordChangeForm.
    """
    pass


