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
        fields = ['name', 'code', 'curator']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название группы'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите код группы'
            }),
            'curator': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'name': 'Название',
            'code': 'Код',
            'curator': 'Куратор',
        }
        help_texts = {
            'code': 'Уникальный код группы',
            'curator': 'Выберите куратора группы (необязательно)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем пользователей для выбора куратора (можно выбрать всех пользователей)
        self.fields['curator'].queryset = User.objects.filter(is_staff=True).order_by('last_name', 'first_name', 'username')
        self.fields['curator'].required = False
        self.fields['curator'].empty_label = 'Не назначен'

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # Проверка уникальности кода (исключая текущий объект при редактировании)
            qs = Group.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Группа с таким кодом уже существует.')
        return code




