from django.contrib.auth import authenticate, get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import UserCreateForm, UserForm

User = get_user_model()


class UserCreationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', is_staff=True)
        self.client.force_login(self.admin)
        self.data = {
            'username': 'new-user',
            'email': 'new@example.com',
            'password1': 'Chosen-secret-794!',
            'password2': 'Chosen-secret-794!',
            'is_active': 'on',
        }

    def test_create_with_chosen_password(self):
        response = self.client.post(reverse('users:user_create'), self.data)
        self.assertRedirects(response, reverse('users:user_management'))
        user = User.objects.get(username=self.data['username'])
        self.assertNotEqual(user.password, self.data['password1'])
        self.assertEqual(
            authenticate(username=user.username, password=self.data['password1']), user
        )
        for message in get_messages(response.wsgi_request):
            self.assertNotIn(self.data['password1'], str(message))

    def test_creation_page_has_masked_password_fields(self):
        response = self.client.get(reverse('users:user_create'))
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, 'type="password"', count=2)

    def test_invalid_passwords_do_not_create_user(self):
        for password2 in ('different-password', ''):
            with self.subTest(password2=password2):
                response = self.client.post(
                    reverse('users:user_create'), {**self.data, 'password2': password2}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn('password2', response.context['form'].errors)
                self.assertFalse(User.objects.filter(username='new-user').exists())
                self.assertNotContains(response, 'value="Chosen-secret-794!"')
        form = UserCreateForm({**self.data, 'password1': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    @override_settings(AUTH_PASSWORD_VALIDATORS=[{
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 20},
    }])
    def test_configured_password_validators_are_applied(self):
        form = UserCreateForm({**self.data, 'password1': 'short', 'password2': 'short'})
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username='existing', email=self.data['email'])
        form = UserCreateForm(self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_edit_preserves_password_without_password_fields(self):
        user = User.objects.create_user(username='existing', password='Existing-secret-12!')
        form = UserForm({'username': user.username, 'first_name': 'Иван'}, instance=user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password('Existing-secret-12!'))
        response = self.client.get(reverse('users:user_edit', args=[user.pk]))
        self.assertNotContains(response, 'name="password1"')
        self.assertNotContains(response, 'name="password2"')
