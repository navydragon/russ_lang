from django import forms
from django.contrib.auth import get_user_model
from .models import Group

User = get_user_model()


class GroupForm(forms.ModelForm):
    """
    Форма для создания и редактирования группы.
    """
    class Meta:
        model = Group
        fields = ['name', 'code', 'curators', 'courses']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название группы'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите код группы'
            }),
            'curators': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8',
            }),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
        }
        labels = {
            'name': 'Название',
            'code': 'Код',
            'curators': 'Кураторы',
        }
        help_texts = {
            'code': 'Уникальный код группы',
            'curators': 'Выберите одного или нескольких кураторов (необязательно)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['code'].disabled = True
        self.fields['curators'].queryset = User.objects.filter(is_tutor=True).order_by('last_name', 'first_name', 'username')
        self.fields['curators'].required = False

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            qs = Group.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Группа с таким кодом уже существует.')
        return code

    def clean_courses(self):
        from .roster import course_ids
        from .portal import PortalError
        courses = self.cleaned_data['courses']
        try:
            course_ids(courses)
        except PortalError as exc:
            raise forms.ValidationError(str(exc)) from None
        return courses


class StudentForm(forms.Form):
    code = forms.CharField(max_length=50, label='Код / логин')
    last_name = forms.CharField(max_length=150, label='Фамилия')
    first_name = forms.CharField(max_length=150, label='Имя')
    middle_name = forms.CharField(max_length=150, required=False, label='Отчество')
    email = forms.EmailField(required=False, label='Почта')
    password = forms.CharField(max_length=128, required=False, strip=False, label='Пароль нового пользователя', widget=forms.PasswordInput,
                               help_text='Для существующего пользователя пароль сохраняется. Пустой пароль нового пользователя будет сгенерирован.')

    def __init__(self, *args, student=None, **kwargs):
        if student:
            kwargs['initial'] = {key: getattr(student, key) for key in ('code', 'last_name', 'first_name', 'middle_name', 'email')}
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        if student:
            self.fields['code'].disabled = True
            self.fields.pop('password')

