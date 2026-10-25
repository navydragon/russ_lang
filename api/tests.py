import re
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from api.reading_check import (
    PHOTO_ALBUM_REFERENCE_TEXT, UNIVERSITY_REFERENCE_TEXT, MOSCOW_REFERENCE_TEXT,
    check_reading_audio, score_reading_from_payload,
)
from api.story_llm import TASK_CONFIGS, StoryCheckResult, StoryError, _build_user_prompt, _sanitize_result


def reading_payload(text=PHOTO_ALBUM_REFERENCE_TEXT, comma_gap=0.25, period_gap=0.5, duration=45):
    words = []
    clock = 0.0
    for token in re.findall(r'\w+|[.,]', text):
        if token == '.':
            clock += period_gap
        elif token == ',':
            clock += comma_gap
        else:
            words.append({'word': token, 'start': round(clock, 3), 'end': round(clock + 0.2, 3)})
            clock += 0.2
    return {'text': text, 'words': words, 'duration': duration}


class PhotoAlbumReadingTests(SimpleTestCase):
    def score(self, payload):
        return score_reading_from_payload(
            payload, PHOTO_ALBUM_REFERENCE_TEXT, max_duration_sec=60,
            coverage_ratio_min=0.60,
            min_comma_pause_sec=0.15, max_comma_pause_sec=0.6,
        )

    def test_complete_reading_with_short_comma_pauses_passes(self):
        result = self.score(reading_payload(duration=60))
        self.assertTrue(result['ok'])
        commas = [p for p in result['pauses']['details'] if p['punctuation'] == ',']
        self.assertEqual(len(commas), 2)
        self.assertTrue(all(p['ok'] for p in commas))
        self.assertEqual(result['coverage']['ratio'], 1.0)

    def test_missing_or_long_comma_pause_fails(self):
        for gap in (0, 0.1, 0.7):
            with self.subTest(gap=gap):
                result = self.score(reading_payload(comma_gap=gap))
                self.assertFalse(result['ok'])
                self.assertFalse(result['pauses']['ok'])

    def test_missing_period_pause_fails(self):
        result = self.score(reading_payload(period_gap=0.1))
        self.assertFalse(result['pauses']['ok'])

    def test_recording_over_one_minute_fails(self):
        result = self.score(reading_payload(duration=60.1))
        self.assertFalse(result['ok'])
        self.assertEqual(result['duration_check']['reason'], 'duration_exceeded')

    def test_missing_word_timestamps_fails(self):
        payload = reading_payload()
        payload.pop('words')
        result = self.score(payload)
        self.assertFalse(result['ok'])
        self.assertEqual(result['pauses']['error'], 'word_timestamps_missing')

    def test_incomplete_reading_fails_coverage(self):
        payload = reading_payload()
        payload['text'] = 'Это моя семья.'
        self.assertFalse(self.score(payload)['coverage']['ok'])

    def test_backend_uses_photo_album_limits_and_reference(self):
        with patch('api.reading_check.transcribe_audio', return_value=reading_payload()) as transcribe:
            result = check_reading_audio(b'audio', 'record.webm', task_id='photo_album')
        self.assertTrue(result['ok'])
        self.assertEqual(result['duration_check']['max_sec'], 60)
        self.assertEqual(result['coverage']['min_ratio'], 0.60)
        self.assertEqual(result['task_id'], 'photo_album')
        self.assertTrue(transcribe.call_args.kwargs['word_timestamps'])

    def test_university_keeps_three_minute_limit_and_period_only_checks(self):
        with patch('api.reading_check.transcribe_audio', return_value=reading_payload(
            text=UNIVERSITY_REFERENCE_TEXT, comma_gap=0, duration=170,
        )):
            result = check_reading_audio(b'audio', 'record.webm', task_id='university')
        self.assertTrue(result['ok'])
        self.assertEqual(result['duration_check']['max_sec'], 180)
        self.assertEqual(result['coverage']['min_ratio'], 0.60)
        self.assertTrue(all(p['punctuation'] == '.' for p in result['pauses']['details']))

    def test_coverage_threshold_includes_exactly_sixty_percent(self):
        reference = 'Раз два три четыре пять.'
        for recognized, expected in [('Раз два три.', True), ('Раз два.', False)]:
            with self.subTest(recognized=recognized):
                result = score_reading_from_payload(
                    reading_payload(text=recognized), reference, coverage_ratio_min=0.60,
                )
                self.assertEqual(result['coverage']['ok'], expected)

    def test_reading_endpoint_accepts_photo_album_task(self):
        with patch('api.reading_check.transcribe_audio', return_value=reading_payload()):
            response = self.client.post('/api/reading/check', {
                'task_id': 'photo_album',
                'file': SimpleUploadedFile('record.webm', b'audio', content_type='audio/webm'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])


class FamilyPhotoWritingTests(SimpleTestCase):
    def test_pass_mark_is_sixty_and_errors_are_preserved(self):
        text = 'Моя отец врач.'
        for score, model_ok, expected in [(59, True, False), (60, False, True), (75, False, True)]:
            with self.subTest(score=score):
                result = StoryCheckResult(
                    ok=model_ok, score=score, feedback='Проверьте согласование', normalized=text,
                    errors=[StoryError(start=0, end=3, code='grammar', message='Нужно «мой».')],
                    quality_notes='Рассказ по теме', recommendations=['Исправьте ошибку.'],
                )
                cleaned = _sanitize_result(result, text, 'family_retelling')
                self.assertEqual(cleaned.ok, expected)
                self.assertEqual(len(cleaned.errors), 1)
                self.assertEqual(cleaned.recommendations, result.recommendations)

    def test_rubric_is_own_family_and_has_no_invented_word_or_sentence_minimum(self):
        cfg = TASK_CONFIGS['family_retelling']
        self.assertEqual(cfg.min_sentences, 0)
        self.assertEqual(cfg.min_vocab_hits, 0)
        prompt = _build_user_prompt('family_retelling', 'Мой текст')
        self.assertIn('Найдите фотографию вашей семьи', prompt)
        self.assertIn('его/её зовут', prompt)
        self.assertNotIn('минимум 0', prompt)
        self.assertNotIn('минимум 3', prompt)

    def test_short_response_is_not_rejected_by_lesson_one_quantitative_rubric(self):
        text = 'Это мой отец, его зовут Иван, он врач.'
        result = StoryCheckResult(
            ok=True, score=100, feedback='Хорошо', normalized=text,
            errors=[], quality_notes='Рассказ по теме', recommendations=[],
        )
        cleaned = _sanitize_result(result, text, 'family_retelling')
        self.assertTrue(cleaned.ok)
        self.assertEqual(cleaned.errors, [])
        # Для старого задания урока 1 его количественные требования сохраняются.
        self.assertFalse(_sanitize_result(result, text, 'family').ok)

    def test_missing_target_construction_remains_a_required_criterion(self):
        text = 'Это моя семья.'
        result = StoryCheckResult(
            ok=False, score=40, feedback='Дополните рассказ', normalized=text,
            errors=[StoryError(start=0, end=len(text), code='completeness', message='Отсутствует конструкция «его/её зовут».')],
            quality_notes='Нужны сведения о членах семьи', recommendations=[],
        )
        cleaned = _sanitize_result(result, text, 'family_retelling')
        self.assertFalse(cleaned.ok)
        self.assertEqual(len(cleaned.errors), 1)


class MyUniversityWritingTests(SimpleTestCase):
    def test_rubric_is_free_writing_without_fixed_reference_or_word_count(self):
        cfg = TASK_CONFIGS['my_university_story']
        self.assertEqual((cfg.min_sentences, cfg.min_vocab_hits), (0, 0))
        self.assertEqual(cfg.passing_score, 60)
        prompt = _build_user_prompt('my_university_story', 'Мой университет большой.')
        self.assertIn('самостоятельный рассказ', prompt)
        self.assertIn('согласование прилагательных', prompt)
        self.assertIn('не требуй писать только о РУТ МИИТ', prompt)

    def test_pass_mark_is_inclusive_and_errors_remain_visible(self):
        text = 'Мой университет большая.'
        for score, expected in [(59, False), (60, True)]:
            result = StoryCheckResult(
                ok=not expected, score=score, feedback='Исправьте согласование.',
                normalized=text, quality_notes='Описание университета',
                errors=[StoryError(start=16, end=23, code='grammar', message='Нужно «большой».')],
                recommendations=[],
            )
            actual = _sanitize_result(result, text, 'my_university_story')
            self.assertEqual(actual.ok, expected)
            self.assertEqual(len(actual.errors), 1)


class MoscowReadingTests(SimpleTestCase):
    def check(self, **kwargs):
        payload = reading_payload(text=MOSCOW_REFERENCE_TEXT, **kwargs)
        with patch('api.reading_check.transcribe_audio', return_value=payload) as asr:
            result = check_reading_audio(b'audio', 'record.webm', task_id='moscow')
        self.assertTrue(asr.call_args.kwargs['word_timestamps'])
        return result

    def test_moscow_uses_three_minutes_sixty_percent_and_period_pauses(self):
        result = self.check(duration=180, comma_gap=0)
        self.assertTrue(result['ok'])
        self.assertEqual(result['title'], 'Москва — столица')
        self.assertEqual(result['duration_check']['max_sec'], 180)
        self.assertEqual(result['coverage']['min_ratio'], 0.60)
        self.assertTrue(all(x['punctuation'] == '.' for x in result['pauses']['details']))

    def test_moscow_rejects_excess_duration_or_missing_period_pauses(self):
        self.assertFalse(self.check(duration=180.1)['ok'])
        self.assertFalse(self.check(period_gap=0.1)['ok'])

    def test_moscow_is_available_through_reading_endpoint(self):
        with patch('api.reading_check.transcribe_audio', return_value=reading_payload(text=MOSCOW_REFERENCE_TEXT)):
            response = self.client.post('/api/reading/check', {
                'task_id': 'moscow', 'file': SimpleUploadedFile('record.webm', b'audio'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
