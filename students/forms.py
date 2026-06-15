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
        fields = ['name', 'code', 'curators']
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
        self.fields['curators'].queryset = User.objects.filter(is_staff=True).order_by('last_name', 'first_name', 'username')
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

