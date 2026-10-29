from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import wave

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from api.university_questions import (
    LIBRARY_QUESTIONS, LIBRARY_TASK_CODE, QUESTIONS, choose_words, grade_answer,
)
from api.test_university_questions import decision
from courses.models import TaskAttempt
from courses.task_catalog import TEST_STUDENT_CODE


@override_settings(LLM_API_KEY='test-key')
class LibraryQuestionBankTests(SimpleTestCase):
    def test_ten_questions_are_selected_from_eleven(self):
        selected = choose_words(LIBRARY_TASK_CODE)
        self.assertEqual(len(selected), 10)
        self.assertEqual(len(set(selected)), 10)
        self.assertTrue(set(selected) <= set(range(1, 12)))

    def test_grader_receives_full_context_and_specific_question_guidance(self):
        for index in (1, 6, 8, 11):
            with patch('api.university_questions._get_agent') as factory:
                factory.return_value.run_sync.return_value.output = decision(True, False)
                result = grade_answer(index, 'Ответ студента.', LIBRARY_TASK_CODE)
            prompt = json.loads(factory.return_value.run_sync.call_args.args[0])
            self.assertEqual(prompt['question'], LIBRARY_QUESTIONS[index-1][0])
            self.assertIn('играют в футбол тут', prompt['source_text'])
            self.assertIn('Слева находится наша библиотека', prompt['source_text'])
            self.assertEqual((result['content_points'], result['writing_points']), (5, 0))
            if index == 6:
                self.assertIn('прямо не названы', prompt['answer_guidance'])
            if index == 8:
                self.assertIn('личное', prompt['answer_guidance'])

    def test_audio_bank_and_stresses_match_the_screenshot_questions(self):
        folder = Path(settings.BASE_DIR) / 'tasks/lesson4/library_questions/audio'
        bank = json.loads((folder / 'questions.json').read_text(encoding='utf-8'))
        self.assertEqual(tuple(item['text'] for item in bank), tuple(q[0] for q in LIBRARY_QUESTIONS))
        for item in bank:
            for word in item['pronunciation']:
                self.assertEqual(word['stressed'].replace('́', ''), word['text'])
                if sum(letter.casefold() in 'аеёиоуыэюя' for letter in word['text']) > 1:
                    self.assertTrue('ё' in word['text'] or word['stressed'].count('́') == 1)
            with wave.open(str(folder / f"{item['id']:02d}.wav")) as sound:
                self.assertGreater(sound.getnframes() / sound.getframerate(), .65)


@override_settings(DEBUG=True)
class LibraryQuestionSessionTests(TestCase):
    def setUp(self):
        call_command('seed_ai_test_data', stdout=StringIO())

    def start(self, code):
        response = self.client.post('/api/university-questions/start', {
            'task_code': code, 'student_code': TEST_STUDENT_CODE,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_two_task_runs_stay_separate_and_restore_their_own_questions(self):
        first = self.start('AI_4_3')
        second = self.start(LIBRARY_TASK_CODE)
        self.assertNotEqual(first['run_id'], second['run_id'])
        for run, questions, directory in ((first, QUESTIONS, 'university_questions'),
                                          (second, LIBRARY_QUESTIONS, 'library_questions')):
            self.assertIn(run['current']['question'], [question[0] for question in questions])
            self.assertIn(f'/{directory}/audio/', run['current']['audio_path'])
            self.assertNotIn('expected', run['current'])
            restored = self.client.get('/api/university-questions/state', {'run_id': run['run_id']}).json()
            self.assertEqual(restored['current'], run['current'])
            self.assertEqual(restored['task_code'], run['task_code'])

    def test_sixty_points_save_only_to_the_library_assignment(self):
        run = self.start(LIBRARY_TASK_CODE)
        for index in range(10):
            text = 'Верный ответ.' if index < 6 else ''
            result = {'question': 'Вопрос?', 'answer': text, 'score': 10 if text else 0,
                      'content_points': 5 if text else 0, 'writing_points': 5 if text else 0}
            with patch('api.university_question_views.grade_answer', return_value=result) as grader:
                response = self.client.post('/api/university-questions/answer', {
                    'run_id': run['run_id'], 'index': index, 'answer': text,
                }, content_type='application/json')
            self.assertEqual(grader.call_args.args[2], LIBRARY_TASK_CODE)
            self.assertEqual(response.status_code, 200)
        final = response.json()
        self.assertEqual(final['score'], 60)
        self.assertTrue(final['ok'])
        self.assertTrue(final['saved'])
        self.client.post('/api/university-questions/answer', {
            'run_id': run['run_id'], 'index': 9, 'answer': '',
        }, content_type='application/json')
        self.assertEqual(TaskAttempt.objects.count(), 1)
        self.assertEqual(TaskAttempt.objects.get().task.code, LIBRARY_TASK_CODE)
