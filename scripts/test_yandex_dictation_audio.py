import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from scripts.generate_yandex_dictation_audio import decode_audio, mark_stress, save_audio, SAMPLE_RATE


class SpeechKitGenerationTests(unittest.TestCase):
    def test_stress_conversion_preserves_case_punctuation_and_yo(self):
        parts = [{'text': 'Это', 'stressed': 'э́то'},
                 {'text': 'словарь', 'stressed': 'слова́рь'},
                 {'text': 'ребёнок', 'stressed': 'ребёнок'}]
        self.assertEqual(mark_stress('Это — словарь, ребёнок!', parts), '+Это — слов+арь, ребёнок!')

    def test_audio_chunks_are_concatenated_in_order(self):
        lines = [json.dumps({'result': {'audioChunk': {'data': base64.b64encode(x).decode()}}}).encode()
                 for x in (b'\x01', b'\x02\x03\x04')]
        self.assertEqual(decode_audio(lines), b'\x01\x02\x03\x04')
        with self.assertRaises(ValueError):
            decode_audio([b'{"error": {"code": 7}}'])
        with self.assertRaises(ValueError):
            decode_audio([])

    def test_prefix_does_not_change_original_speech(self):
        pcm = b'\x01\x02' * SAMPLE_RATE
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / 'sample.wav'
            save_audio(path, pcm)
            with wave.open(str(path)) as sound:
                self.assertEqual(sound.getframerate(), SAMPLE_RATE)
                self.assertEqual(sound.getnchannels(), 1)
                data = sound.readframes(sound.getnframes())
                cue_size = round(SAMPLE_RATE * .15) * 2
                pause_size = round(SAMPLE_RATE * .5) * 2
                self.assertTrue(any(data[:cue_size]))
                self.assertEqual(data[cue_size:cue_size + pause_size], bytes(pause_size))
                self.assertEqual(data[cue_size + pause_size:], pcm)

    def test_bulk_failure_preserves_lessons_and_resume_reuses_cache(self):
        import scripts.generate_yandex_dictation_audio as generator
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            root = Path(directory)
            targets = [root / 'tasks/lesson3' / task / 'audio/01.wav' for task in ('one', 'two')]
            for target in targets:
                target.parent.mkdir(parents=True)
                target.write_bytes(b'original')
            with patch.object(generator, 'ROOT', root), patch.object(generator, 'TASK_DIRECTORIES', ('one', 'two')), \
                 patch.object(generator, 'task_items', return_value=[(1, 'sample')]):
                with patch.object(generator, 'synthesize', side_effect=[b'\x01\x02' * 100, RuntimeError('offline')]):
                    with self.assertRaises(RuntimeError):
                        generator.generate_all('not-a-real-key', 'marina', 'friendly', .7, True)
                self.assertTrue(all(target.read_bytes() == b'original' for target in targets))
                with patch.object(generator, 'synthesize', return_value=b'\x01\x02' * 100) as request:
                    generator.generate_all('not-a-real-key', 'marina', 'friendly', .7, True)
                    self.assertEqual(request.call_count, 1)
                self.assertTrue(all(target.read_bytes().startswith(b'RIFF') for target in targets))
                backups = list((root / '.speechkit-cache/backups').glob('*/tasks/lesson3/*/audio/01.wav'))
                self.assertEqual(len(backups), 2)
                self.assertTrue(all(path.read_bytes() == b'original' for path in backups))


if __name__ == '__main__':
    unittest.main()
