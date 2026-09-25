from __future__ import annotations

import re
from typing import Any, Optional

from .speaking_nexara import (
    extract_recognized_text,
    extract_word_timestamps,
    normalize_ru,
    tokenize_ru,
    transcribe_audio,
)

TASK_ID_UNIVERSITY = 'university'
MAX_DURATION_SEC = 180.0
MIN_PAUSE_SEC = 0.30
COVERAGE_TOKEN_RATIO = 0.85

UNIVERSITY_REFERENCE_TEXT = (
    'Вот наш университет. Это большое здание. Вот вход. Это первый этаж. '
    'Здесь красивый зал. Тут сейчас интересная лекция. '
    'Справа новая библиотека, а слева – наша столовая.\n'
    'А это третий этаж. Это механический факультет. Здесь большие и маленькие аудитории. '
    'Там новые столы и стулья. Вот иностранные студенты, а там – наш деканат.\n'
    'Недалеко спортивный комплекс. Здесь наши спортсмены и спортсменки. '
    'Там спортивные залы, новый бассейн и теннисные корты.\n'
    'Рядом студенческий городок. Здесь студенческое общежитие, интернациональный клуб, '
    'большая столовая и маленькое кафе.'
)

READING_TASKS: dict[str, dict[str, Any]] = {
    TASK_ID_UNIVERSITY: {
        'title': 'Наш университет',
        'reference_text': UNIVERSITY_REFERENCE_TEXT,
    },
}


def split_sentences(text: str) -> list[str]:
    """Split on sentence-ending periods; keep non-empty trimmed sentences."""
    parts = re.split(r'(?<=\.)\s+', (text or '').strip())
    return [p.strip() for p in parts if p.strip()]


def period_boundary_token_indices(reference_text: str) -> list[dict[str, Any]]:
    """
    For each sentence that ends with '.' and has a following sentence,
    return the reference token index of the last token of the current sentence.
    """
    sentences = split_sentences(reference_text)
    boundaries: list[dict[str, Any]] = []
    token_offset = 0
    for i, sentence in enumerate(sentences):
        tokens = tokenize_ru(sentence)
        if not tokens:
            continue
        last_idx = token_offset + len(tokens) - 1
        ends_with_period = sentence.rstrip().endswith('.')
        has_next = i + 1 < len(sentences) and bool(tokenize_ru(sentences[i + 1]))
        if ends_with_period and has_next:
            boundaries.append({
                'after_sentence_index': i,
                'after_token_index': last_idx,
                'sentence_preview': sentence[:80],
            })
        token_offset += len(tokens)
    return boundaries


def coverage_ratio(recognized: str, reference_text: str) -> float:
    ref_tokens = set(tokenize_ru(reference_text))
    if not ref_tokens:
        return 0.0
    rec_tokens = set(tokenize_ru(recognized))
    hit = sum(1 for t in ref_tokens if t in rec_tokens)
    return hit / len(ref_tokens)


def align_reference_to_words(
    reference_text: str,
    words: list[dict[str, Any]],
) -> list[Optional[dict[str, Any]]]:
    """
    Greedy sequential alignment: for each reference token, find the next ASR word
    whose normalized form equals (or contains) the token.
    """
    ref_tokens = tokenize_ru(reference_text)
    aligned: list[Optional[dict[str, Any]]] = []
    cursor = 0
    norm_asr = [(normalize_ru(w['word']), w) for w in words]

    for token in ref_tokens:
        matched: Optional[dict[str, Any]] = None
        while cursor < len(norm_asr):
            nw, wobj = norm_asr[cursor]
            cursor += 1
            if nw == token or token in nw or nw in token:
                matched = wobj
                break
        aligned.append(matched)
    return aligned


def score_period_pauses(
    reference_text: str,
    words: list[dict[str, Any]],
    min_pause_sec: float = MIN_PAUSE_SEC,
) -> dict[str, Any]:
    boundaries = period_boundary_token_indices(reference_text)
    aligned = align_reference_to_words(reference_text, words)
    details: list[dict[str, Any]] = []
    all_ok = True

    if not boundaries:
        return {
            'ok': False,
            'details': [],
            'count': 0,
            'error': 'no_period_boundaries',
        }

    for b in boundaries:
        idx = b['after_token_index']
        prev = aligned[idx] if idx < len(aligned) else None
        nxt = None
        for j in range(idx + 1, len(aligned)):
            if aligned[j] is not None:
                nxt = aligned[j]
                break

        if prev is None or nxt is None:
            all_ok = False
            details.append({
                'after_sentence_index': b['after_sentence_index'],
                'sentence_preview': b['sentence_preview'],
                'gap_sec': None,
                'ok': False,
                'reason': 'alignment_failed',
            })
            continue

        gap = float(nxt['start']) - float(prev['end'])
        pause_ok = gap >= min_pause_sec
        if not pause_ok:
            all_ok = False
        details.append({
            'after_sentence_index': b['after_sentence_index'],
            'sentence_preview': b['sentence_preview'],
            'gap_sec': round(gap, 3),
            'ok': pause_ok,
            'min_pause_sec': min_pause_sec,
        })

    return {'ok': all_ok, 'details': details, 'count': len(details)}


def score_reading_from_payload(
    payload: dict[str, Any],
    reference_text: str,
    max_duration_sec: float = MAX_DURATION_SEC,
    min_pause_sec: float = MIN_PAUSE_SEC,
    coverage_ratio_min: float = COVERAGE_TOKEN_RATIO,
) -> dict[str, Any]:
    recognized = extract_recognized_text(payload)
    words = extract_word_timestamps(payload)
    ratio = coverage_ratio(recognized, reference_text)
    coverage_ok = ratio >= coverage_ratio_min

    duration = payload.get('duration')
    duration_ok = False
    duration_reason: Optional[str] = None
    duration_value: Optional[float] = None
    if duration is None:
        duration_reason = 'duration_missing'
    else:
        try:
            duration_value = float(duration)
            duration_ok = duration_value <= max_duration_sec
            if not duration_ok:
                duration_reason = 'duration_exceeded'
        except (TypeError, ValueError):
            duration_reason = 'duration_invalid'

    if not words:
        pauses: dict[str, Any] = {
            'ok': False,
            'details': [],
            'count': 0,
            'error': 'word_timestamps_missing',
        }
        pauses_ok = False
    else:
        pauses = score_period_pauses(reference_text, words, min_pause_sec=min_pause_sec)
        pauses_ok = bool(pauses.get('ok'))

    ok = coverage_ok and duration_ok and pauses_ok
    return {
        'ok': ok,
        'recognized': recognized,
        'duration': duration_value,
        'coverage': {
            'ok': coverage_ok,
            'ratio': round(ratio, 4),
            'min_ratio': coverage_ratio_min,
        },
        'duration_check': {
            'ok': duration_ok,
            'max_sec': max_duration_sec,
            'reason': duration_reason,
        },
        'pauses': pauses,
    }


def check_reading_audio(
    file_bytes: bytes,
    filename: str,
    task_id: str = TASK_ID_UNIVERSITY,
    content_type: str = 'application/octet-stream',
    language: str = 'ru',
) -> dict[str, Any]:
    task = READING_TASKS.get(task_id)
    if not task:
        raise ValueError(f'Unknown reading task_id: {task_id}')

    payload = transcribe_audio(
        file_bytes,
        filename,
        content_type=content_type,
        language=language,
        word_timestamps=True,
    )
    result = score_reading_from_payload(payload, task['reference_text'])
    result['task_id'] = task_id
    result['title'] = task['title']
    language_out = payload.get('language')
    if language_out:
        result['language'] = language_out
    return result
