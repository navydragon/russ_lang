"""Measure uploaded audio duration by decoding it with the bundled FFmpeg."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path


class AudioDurationError(RuntimeError):
    pass


def measure_audio_duration(file_bytes: bytes, filename: str = 'record.webm') -> float:
    if not file_bytes:
        raise AudioDurationError('Аудиозапись пуста.')
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise AudioDurationError('На сервере недоступен измеритель длительности аудио.') from exc

    suffix = Path(filename or '').suffix.lower()
    if not re.fullmatch(r'\.[a-z0-9]{1,8}', suffix):
        suffix = '.audio'
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(file_bytes)
            path = temp.name
        result = subprocess.run(
            [ffmpeg, '-hide_banner', '-nostats', '-i', path, '-map', '0:a:0',
             '-f', 'null', '-', '-progress', 'pipe:1'],
            capture_output=True, text=True, timeout=45, check=False,
        )
        if result.returncode:
            raise AudioDurationError('Не удалось определить длительность аудиозаписи. Запишите её ещё раз.')
        matches = re.findall(r'^out_time_us=(\d+)$', result.stdout, re.MULTILINE)
        if not matches or int(matches[-1]) <= 0:
            raise AudioDurationError('Не удалось определить длительность аудиозаписи. Запишите её ещё раз.')
        return int(matches[-1]) / 1_000_000
    except subprocess.TimeoutExpired as exc:
        raise AudioDurationError('Проверка длительности аудио превысила время ожидания.') from exc
    except OSError as exc:
        raise AudioDurationError('Не удалось запустить измеритель длительности аудио.') from exc
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass
