from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from api.retelling_check import MAX_AUDIO_BYTES


class SpeakingEndpointTests(SimpleTestCase):
    @patch('api.views.check_speaking_audio')
    def test_classroom_recording_reaches_transcription(self, check_audio):
        check_audio.return_value = {
            'ok': True, 'recognized': 'доска', 'reference': 'доска',
        }
        recording = SimpleUploadedFile('record.webm', b'valid recording', content_type='audio/webm')
        response = self.client.post('/api/speaking/check', {
            'file': recording, 'reference': 'доска', 'language': 'ru',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recognized'], 'доска')
        check_audio.assert_called_once_with(
            file_bytes=b'valid recording', filename='record.webm',
            reference='доска', content_type='audio/webm', language='ru',
        )

    @patch('api.views.check_speaking_audio')
    def test_oversized_recording_is_rejected_before_transcription(self, check_audio):
        recording = SimpleUploadedFile('record.webm', b'x' * (MAX_AUDIO_BYTES + 1), content_type='audio/webm')
        response = self.client.post('/api/speaking/check', {'file': recording, 'reference': 'доска'})
        self.assertEqual(response.status_code, 413)
        check_audio.assert_not_called()
