from django.test import SimpleTestCase, override_settings

from courses.task_catalog import TASK_CATALOG


class AuthorReviewTests(SimpleTestCase):
    @override_settings(DEBUG=False)
    def test_public_page_lists_ready_tasks_without_identity_or_database(self):
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
