from django.test import SimpleTestCase
from api.reading_check import DIALOGUE_REFERENCES, READING_TASKS, score_reading_from_payload
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
