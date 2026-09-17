from __future__ import annotations

import logging
import re
from typing import Any, Optional

import httpx
from django.conf import settings

logger = logging.getLogger('api')


def normalize_ru(text: str) -> str:
    s = (text or '').lower().replace('ё', 'е')
    s = re.sub(r'[^\w\s]+', ' ', s, flags=re.UNICODE)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def reference_matched(recognized: str, reference: str) -> bool:
    ref = normalize_ru(reference)
    if not ref:
        return False
    return ref in normalize_ru(recognized)


def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    content_type: str = 'application/octet-stream',
    language: str = 'ru',
) -> dict[str, Any]:
    """
    Call Nexara audio/transcriptions with response_format=verbose_json.
    Returns parsed JSON (expects at least 'text').
    """
    api_key = settings.NEXARA_API_KEY
    if not api_key:
        raise RuntimeError('NEXARA_API_KEY is not configured')

    url = f'{settings.NEXARA_BASE_URL}/audio/transcriptions'
    headers = {'Authorization': f'Bearer {api_key}'}
    data = {
        'model': settings.NEXARA_MODEL,
        'response_format': 'verbose_json',
        'language': language or 'ru',
    }
    files = {
        'file': (filename or 'audio.webm', file_bytes, content_type or 'application/octet-stream'),
    }

    logger.info('Nexara transcription: url=%s filename=%s bytes=%d', url, filename, len(file_bytes))
    with httpx.Client(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        response = client.post(url, headers=headers, data=data, files=files)

    if response.status_code >= 400:
        logger.error('Nexara error HTTP %s: %s', response.status_code, response.text[:500])
        raise RuntimeError(f'Nexara transcription failed: HTTP {response.status_code}')

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError('Nexara returned non-JSON object')
    return payload


def extract_recognized_text(payload: dict[str, Any]) -> str:
    text = payload.get('text')
    if isinstance(text, str):
        return text.strip()
    return ''


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
