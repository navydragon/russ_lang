from django.test import TestCase, override_settings

from courses.task_catalog import TASK_CATALOG


class AuthorReviewTests(TestCase):
    @override_settings(DEBUG=False)
    def test_public_page_lists_ready_tasks_without_identity(self):
        response = self.client.get('/authors/assignments/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        ready = [item for item in TASK_CATALOG if item.html_path]
        self.assertEqual(html.count('class="open"'), len(ready))
        for item in ready:
            self.assertIn(item.code, html)
            self.assertIn('/tasks/' + item.html_path, html)
        self.assertIn('target="_blank" rel="noopener noreferrer"', html)
        self.assertIn('Что делает студент', html)
        self.assertIn('Что делает ИИ', html)
        self.assertNotIn('AI_TEST_STUDENT', html)
        self.assertNotIn('student_code=', html)
        self.assertNotIn('student_code', response.cookies)
        self.assertNotIn('AI_4_14', html)

    @override_settings(DEBUG=False)
    def test_public_confirmation_is_shared_and_reversible(self):
        from django.test import Client
        other = Client()
        url = '/authors/assignments/confirmation/'
        self.assertEqual(self.client.post(url, {'task_code': 'AI_1_4', 'confirmed': 'true'}).status_code, 200)
        page = other.get('/authors/assignments/')
        self.assertContains(page, 'Внесены правки · 10.11.2026')
        self.assertContains(page, 'name="confirmed" checked')
        self.assertEqual(other.post(url, {'task_code': 'AI_1_4', 'confirmed': 'false'}).status_code, 200)
        self.assertNotContains(self.client.get('/authors/assignments/'), 'name="confirmed" checked')
        self.assertEqual(other.post(url, {'task_code': 'unknown', 'confirmed': 'true'}).status_code, 400)
