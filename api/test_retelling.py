from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from api.retelling_check import check_retelling_audio
from api.story_llm import StoryCheckResult, _build_user_prompt, _sanitize_result


def retelling_result(score=75):
    return StoryCheckResult(
        ok=score >= 60, score=score, feedback='Основная информация передана.',
        normalized='Вот наш университет. Рядом общежитие.', errors=[],
        quality_notes='Связный пересказ.', recommendations=[],
    )


class RetellingTests(SimpleTestCase):
    def test_moscow_audio_uses_its_own_rubric(self):
        transcript = 'Москва — красивый город. В центре Кремль. В Москве удобное метро.'
        with patch('api.retelling_check.transcribe_audio', return_value={'text': transcript}), patch(
            'api.retelling_check.check_story', return_value=retelling_result(),
        ) as grader:
            result, details = check_retelling_audio(b'audio', 'record.webm', task_id='moscow_retelling')
        self.assertEqual(grader.call_args.args, ('moscow_retelling', transcript))
        self.assertEqual(details['passing_score'], 60)
        self.assertEqual(details['recognized'], transcript)

    def test_moscow_prompt_contains_three_blocks_and_inclusive_pass_mark(self):
        prompt = _build_user_prompt('moscow_retelling', 'Мой пересказ')
        for text in ['Москва — красивый город', 'Вот центр Москвы', 'Москва — это удобный город', 'Проходной балл: 60']:
            self.assertIn(text, prompt)
        for score, expected in [(59, False), (60, True)]:
            result = retelling_result(score)
            result.ok = not expected
            self.assertEqual(_sanitize_result(result, result.normalized, 'moscow_retelling').ok, expected)

    def test_moscow_code_cannot_be_used_with_university_rubric(self):
        with patch('api.views.check_retelling_audio') as check:
            response = self.client.post('/api/retelling/check', {
                'task_id': 'university_retelling', 'task_code': 'AI_3_6',
                'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 400)
        check.assert_not_called()

    def test_asr_text_goes_to_semantic_check_and_stress_is_not_fabricated(self):
        transcript = 'Вот наш университет. Рядом общежитие.'
        with patch('api.retelling_check.transcribe_audio', return_value={
            'text': transcript, 'duration': 42,
        }) as asr, patch('api.retelling_check.check_story', return_value=retelling_result()) as grader:
            result, details = check_retelling_audio(b'audio', 'record.webm')
        self.assertEqual(grader.call_args.args, ('university_retelling', transcript))
        self.assertEqual(details['recognized'], transcript)
        self.assertEqual(details['stress_check']['status'], 'not_assessed')
        self.assertEqual(details['duration'], 42)
        self.assertTrue(result.ok)
        self.assertNotIn('word_timestamps', asr.call_args.kwargs)

    def test_no_speech_does_not_call_grader(self):
        with patch('api.retelling_check.transcribe_audio', return_value={'text': ' '}) as asr, patch('api.retelling_check.check_story') as grader:
            with self.assertRaises(ValueError):
                check_retelling_audio(b'audio', 'record.webm')
        grader.assert_not_called()

    def test_empty_audio_does_not_call_asr(self):
        with patch('api.retelling_check.transcribe_audio') as asr:
            with self.assertRaises(ValueError):
                check_retelling_audio(b'', 'record.webm')
        asr.assert_not_called()

    def test_rubric_accepts_floor_variants_and_does_not_claim_stress_assessment(self):
        prompt = _build_user_prompt('university_retelling', 'Наш университет.')
        self.assertIn('принимай оба варианта', prompt)
        self.assertIn('не оценивай', prompt)
        self.assertIn('Проходной балл: 60', prompt)

    def test_pass_boundary_is_enforced_on_server(self):
        for score, expected in [(59, False), (60, True)]:
            result = retelling_result(score)
            result.ok = not expected
            actual = _sanitize_result(result, result.normalized, 'university_retelling')
            self.assertEqual(actual.ok, expected)

    def test_endpoint_requires_audio_and_the_right_assignment_code(self):
        self.assertEqual(self.client.post('/api/retelling/check', {}).status_code, 400)
        with patch('api.views.check_retelling_audio') as check:
            response = self.client.post('/api/retelling/check', {
                'task_id': 'university_retelling', 'task_code': 'AI_3_1',
                'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 400)
        check.assert_not_called()

    def test_written_story_endpoint_does_not_replace_the_audio_task(self):
        response = self.client.post('/api/story/check', {
            'task_id': 'university_retelling', 'text': 'Готовый текст.',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class NovgorodRetellingTests(SimpleTestCase):
    def test_audio_uses_novgorod_rubric_and_actual_transcript(self):
        transcript = 'Я студент и историк. Мой родной город Новгород.'
        with patch('api.retelling_check.transcribe_audio', return_value={'text': transcript, 'duration': 30}), patch(
            'api.retelling_check.check_story', return_value=retelling_result(),
        ) as grader:
            result, details = check_retelling_audio(b'audio', 'record.webm', task_id='novgorod_retelling')
        grader.assert_called_once_with('novgorod_retelling', transcript)
        self.assertEqual(details['recognized'], transcript)
        self.assertEqual(details['stress_check']['status'], 'not_assessed')
        self.assertEqual(details['passing_score'], 60)

    def test_prompt_contains_full_source_six_blocks_and_pass_threshold(self):
        from api.dictation import NOVGOROD_SENTENCES
        prompt = _build_user_prompt('novgorod_retelling', 'Мой пересказ')
        for sentence in NOVGOROD_SENTENCES:
            self.assertIn(sentence, prompt)
        for fragment in ('Я…', 'История — это…', 'Новгород — это…',
                         'Исторический центр города — это…', 'Моя семья — это…',
                         'Вот наша улица, здесь…', 'Проходной балл: 60', 'перефразирование'):
            self.assertIn(fragment, prompt)
        for score in (59, 60):
            result = retelling_result(score)
            result.ok = not (score >= 60)
            self.assertEqual(_sanitize_result(result, result.normalized, 'novgorod_retelling').ok, score >= 60)

    def test_wrong_assignment_and_written_bypass_are_rejected(self):
        with patch('api.views.check_retelling_audio') as check:
            response = self.client.post('/api/retelling/check', {
                'task_id': 'novgorod_retelling', 'task_code': 'AI_3_10',
                'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 400)
        check.assert_not_called()
        response = self.client.post('/api/story/check', {
            'task_id': 'novgorod_retelling', 'task_code': 'AI_3_11', 'text': 'Готовый текст.'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
