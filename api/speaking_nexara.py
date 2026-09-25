from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger('api')


def normalize_ru(text: str) -> str:
    s = (text or '').lower().replace('ё', 'е')
    s = re.sub(r'[^\w\s]+', ' ', s, flags=re.UNICODE)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def tokenize_ru(text: str) -> list[str]:
    return [t for t in normalize_ru(text).split() if t]


def reference_matched(recognized: str, reference: str) -> bool:
    ref = normalize_ru(reference)
    if not ref:
        return False
    return ref in normalize_ru(recognized)


def extract_recognized_text(payload: dict[str, Any]) -> str:
    text = payload.get('text')
    if isinstance(text, str):
        return text.strip()
    return ''


def extract_word_timestamps(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract [{word, start, end}, ...] from Nexara/OpenAI-style verbose_json.
    Prefers top-level `words`; falls back to concatenating segment words.
    """
    raw_words = payload.get('words')
    if not isinstance(raw_words, list):
        raw_words = []
        segments = payload.get('segments')
        if isinstance(segments, list):
            for seg in segments:
                if isinstance(seg, dict) and isinstance(seg.get('words'), list):
                    raw_words.extend(seg['words'])

    result: list[dict[str, Any]] = []
    for item in raw_words:
        if not isinstance(item, dict):
            continue
        word = item.get('word')
        if word is None:
            word = item.get('text')
        if not isinstance(word, str) or not word.strip():
            continue
        start = item.get('start')
        end = item.get('end')
        try:
            start_f = float(start)
            end_f = float(end)
        except (TypeError, ValueError):
            continue
        result.append({'word': word.strip(), 'start': start_f, 'end': end_f})
    return result


def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    content_type: str = 'application/octet-stream',
    language: str = 'ru',
    word_timestamps: bool = False,
) -> dict[str, Any]:
    """
    Call Nexara audio/transcriptions with response_format=verbose_json.
    Returns parsed JSON (expects at least 'text').
    """
    try:
        return _transcribe_audio_once(
            file_bytes,
            filename,
            content_type=content_type,
            language=language,
            word_timestamps=word_timestamps,
        )
    except RuntimeError as e:
        # Word timestamps are optional for basic ASR; retry without them.
        if word_timestamps and 'NEXARA_API_KEY' not in str(e):
            logger.warning('Nexara with word timestamps failed (%s); retrying without', e)
            return _transcribe_audio_once(
                file_bytes,
                filename,
                content_type=content_type,
                language=language,
                word_timestamps=False,
            )
        raise


def _transcribe_audio_once(
    file_bytes: bytes,
    filename: str,
    content_type: str = 'application/octet-stream',
    language: str = 'ru',
    word_timestamps: bool = False,
) -> dict[str, Any]:
    api_key = settings.NEXARA_API_KEY
    if not api_key:
        raise RuntimeError('NEXARA_API_KEY is not configured')

    url = f'{settings.NEXARA_BASE_URL}/audio/transcriptions'
    headers = {'Authorization': f'Bearer {api_key}'}
    data: dict[str, Any] = {
        'model': settings.NEXARA_MODEL,
        'response_format': 'verbose_json',
        'language': language or 'ru',
    }
    if word_timestamps:
        # Nexara/OpenAI: array field in multipart
        data['timestamp_granularities[]'] = 'word'

    files = {
        'file': (filename or 'audio.webm', file_bytes, content_type or 'application/octet-stream'),
    }

    logger.info(
        'Nexara transcription: url=%s filename=%s bytes=%d word_timestamps=%s',
        url,
        filename,
        len(file_bytes),
        word_timestamps,
    )
    try:
        with httpx.Client(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            response = client.post(url, headers=headers, data=data, files=files)
    except httpx.TimeoutException as e:
        logger.exception('Nexara timeout: %s', e)
        raise RuntimeError('Nexara transcription timed out') from e
    except httpx.HTTPError as e:
        logger.exception('Nexara transport error: %s', e)
        raise RuntimeError(f'Nexara request failed: {e}') from e

    if response.status_code >= 400:
        logger.error('Nexara error HTTP %s: %s', response.status_code, response.text[:500])
        raise RuntimeError(f'Nexara transcription failed: HTTP {response.status_code}')

    try:
        payload = response.json()
    except ValueError as e:
        logger.error('Nexara non-JSON body: %s', response.text[:500])
        raise RuntimeError('Nexara returned non-JSON body') from e
    if not isinstance(payload, dict):
        raise RuntimeError('Nexara returned non-JSON object')
    return payload


def check_speaking_audio(
    file_bytes: bytes,
    filename: str,
    reference: str,
    content_type: str = 'application/octet-stream',
    language: str = 'ru',
) -> dict[str, Any]:
    payload = transcribe_audio(file_bytes, filename, content_type=content_type, language=language)
    recognized = extract_recognized_text(payload)
    ok = reference_matched(recognized, reference)
    result: dict[str, Any] = {
        'ok': ok,
        'recognized': recognized,
        'reference': reference,
    }
    duration = payload.get('duration')
    if duration is not None:
        result['duration'] = duration
    segments = payload.get('segments')
    if isinstance(segments, list):
        result['segments'] = segments
    language_out = payload.get('language')
    if language_out:
        result['language'] = language_out
    return result
