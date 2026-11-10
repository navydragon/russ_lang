from django.test import SimpleTestCase
from unittest.mock import patch
from api.reading_check import DIALOGUE_REFERENCES, READING_TASKS, score_reading_from_payload, check_reading_audio
from api.test_lesson4_reading import payload

class DialogueReadingTests(SimpleTestCase):
    def test_four_dialogues_have_separate_references_and_two_minute_limit(self):
        for index, reference in enumerate(DIALOGUE_REFERENCES, 1):
            task = READING_TASKS[f'lesson4_dialogue_{index}']
            self.assertEqual(task['reference_text'], reference)
            self.assertEqual(task['max_duration_sec'], 120)
            for duration, expected in ((120, True), (121, False)):
                result = score_reading_from_payload(payload(duration=duration, reference=reference), reference, max_duration_sec=120, sentence_endings='.?!')
                self.assertEqual(result['duration_check']['ok'], expected)

    def test_complete_reading_uses_file_duration_for_all_requested_dialogues(self):
        for task_id in ('lesson4_dialogue_3', 'lesson4_introduction_dialogue', 'lesson4_free_time_dialogue'):
            with self.subTest(task_id=task_id):
                reference = READING_TASKS[task_id]['reference_text']
                transcription = payload(duration=999, reference=reference)
                with patch('api.reading_check.measure_audio_duration', return_value=30), patch('api.reading_check.transcribe_audio', return_value=transcription):
                    result = check_reading_audio(b'audio', 'record.webm', task_id=task_id)
                self.assertTrue(result['ok'])
                self.assertEqual(result['duration'], 30)
                self.assertGreaterEqual(result['score'], 60)

    def test_measured_duration_over_limit_is_not_accepted(self):
        task_id = 'lesson4_dialogue_3'
        reference = READING_TASKS[task_id]['reference_text']
        with patch('api.reading_check.measure_audio_duration', return_value=121), patch('api.reading_check.transcribe_audio', return_value=payload(duration=30, reference=reference)):
            result = check_reading_audio(b'audio', 'record.webm', task_id=task_id)
        self.assertFalse(result['ok'])
        self.assertEqual(result['duration_check']['reason'], 'duration_exceeded')
