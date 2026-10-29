from __future__ import annotations

import logging
import re
import math
from difflib import SequenceMatcher
from typing import Any, Optional

from .speaking_nexara import (
    extract_recognized_text,
    extract_word_timestamps,
    normalize_ru,
    tokenize_ru,
    transcribe_audio,
)

logger = logging.getLogger('api')

TASK_ID_UNIVERSITY = 'university'
MAX_DURATION_SEC = 180.0
MIN_PAUSE_SEC = 0.30
COVERAGE_TOKEN_RATIO = 0.60
TASK_ID_PHOTO_ALBUM = 'photo_album'
MIN_COMMA_PAUSE_SEC = 0.15
MAX_COMMA_PAUSE_SEC = 0.60

PHOTO_ALBUM_REFERENCE_TEXT = (
    'Это я. Это моя семья. Это мой отец. Его зовут Владимир Петрович. Он инженер. '
    'А это моя мать. Её зовут Тамара Ивановна. Она врач. '
    'Это мой брат, его зовут Саша. Он студент. '
    'А это моя сестра, её зовут Наташа. Она тоже студентка.'
)

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

MOSCOW_REFERENCE_TEXT = (
    'Москва – большой и красивый город. Здесь есть широкие улицы новые проспекты, '
    'современные высокие здания, красивые площади, старые тихие улицы. Вот Красная площадь.\n'
    'А вот Московский Кремль. Это центр города. Здесь Большой театр. Я люблю русский балет. '
    'А это Московский университет. Здесь русские и иностранные студенты.\n'
    'Москва – зелёный город, здесь большие парки и красивые сады. А это московское метро. '
    'Оно самое удобное, красивое и быстрое.'
)

LESSON4_UNIVERSITY_REFERENCE_PARTS = ('Это мой университет. Здесь мои друзья. Это Антон, Виктор и Андрей.\nЯ студент и мои друзья тоже студенты. Вот наша аудитория, здесь утром мы работаем.\nСправа наш преподаватель, он понятно объясняет урок, а мы внимательно слушаем, как говорит преподаватель.\nПотом преподаватель спрашивает: «Вы всё понимаете?»\nАнна спрашивает: «Что значит слово „глагол“?» Преподаватель отвечает: «Глаголы — это слова, они отвечают на вопрос: что делать? Например: что делать? — писать». «Спасибо, — отвечает Анна, — сейчас я всё понимаю».\nВот справа наш спортзал. Здесь после урока наши студенты и студентки играют в баскетбол. Мой друг Виктор — футболист, он и его друзья часто вечером играют в футбол тут.', 'Слева находится наша библиотека. Здесь все студенты занимаются после урока. Вот столы, лампы, книги, учебники, тетради, словари и журналы.\nЗдесь Виктор и Антон делают уроки, они читают тексты, пишут упражнения, учат слова. Они — друзья, и они помогают друг другу.\nА это наша столовая. Тут утром мы завтракаем, днём обедаем, а вечером ужинаем. Вот наш стол. Сейчас обед, здесь суп, борщ, салат, мясо, рыба, хлеб, сок.\nТам наше общежитие. Здесь все мои друзья отдыхают после урока. Это наша комната № 5.\nСправа наш шкаф, тут мой пиджак, брюки, куртка и пальто. Там наш стол, здесь наши книги и тетради. Слева окно, тут моя кровать, это моя подушка и моё одеяло. Мы любим наш университет.')
LESSON4_UNIVERSITY_REFERENCE_TEXT = "\n\n".join(LESSON4_UNIVERSITY_REFERENCE_PARTS)

NEIGHBORHOOD_REFERENCE_TEXT = 'Это наш район, здесь наш дом. Район красивый, зелёный, недалеко находится лес, мы часто гуляем вместе там. Наш район новый, но здесь уже есть метро, это очень удобно.\nА это наша улица. Дома здесь новые, высокие. Вот больница номер двадцать три. Здесь работает Нина Петровна. Слева двадцатая школа, где учится Таня. Она любит изучать иностранный язык, Таня уже хорошо говорит по-английски и переводит английские тексты.\nСправа находятся магазины и кинотеатр. Вот одиннадцатый дом, где мы живём, а там дом номер двенадцать, где живут мои друзья. Я иногда бываю там.'

DIALOGUE_REFERENCES = ('Вы говорите по-русски?\nДа, говорю. Где группа номер четыре?\nЯ не понимаю, когда вы говорите быстро.', 'Ребята! Когда вы обедаете?\nОбычно мы обедаем после урока.\nЧто вы делаете потом?\nГуляем. Почему ты спрашиваешь?\nПотому что сегодня днём футбол.', 'Что это? Аудитория?\nНет, это деканат.\nГде аудитория номер три?\nСправа.', 'Лилия, ты ещё учишь слова?\nНет, я уже делаю упражнение.\nА я перевожу текст. Не знаю, что значит это слово. Ты не знаешь?\nТоже не знаю.')

LESSON4_INTRODUCTION_DIALOGUE = 'Здравствуйте, Сергей Иванович!\nЗдравствуйте!\nСергей Иванович, познакомьтесь, пожалуйста. Это мой друг Джон. Джон, это мой русский преподаватель, Сергей Иванович.\nОчень приятно!\nОчень приятно!\nДжон, вы студент?\nНет, я уже работаю. Я инженер.\nДрузья, вы любите кофе?\nДа, конечно.\nВот, пожалуйста.\nБольшое спасибо.'

LESSON4_FREE_TIME_DIALOGUE = 'Что вы делаете в свободное время?\nЧитаем. Слушаем музыку.\nСмотрим фильм.\nА вы смотрите русские фильмы?\nИногда.\nЯ думаю, что вы часто смотрите спорт.\nКонечно. Особенно футбол.\nДжон, вы неплохо говорите по-русски. Вы давно изучаете русский язык?\nНет, нет. Что вы! Я плохо говорю, но я работаю. Читаю по-русски, слушаю, смотрю фильмы.\nИ всё понимаете?\nКонечно, нет.'

READING_TASKS: dict[str, dict[str, Any]] = {
    'lesson4_free_time_dialogue': {'title': 'Свободное время', 'reference_text': LESSON4_FREE_TIME_DIALOGUE, 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'lesson4_introduction_dialogue': {'title': 'Знакомство', 'reference_text': LESSON4_INTRODUCTION_DIALOGUE, 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'lesson4_dialogue_1': {'title': 'Диалог 1', 'reference_text': DIALOGUE_REFERENCES[0], 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'lesson4_dialogue_2': {'title': 'Диалог 2', 'reference_text': DIALOGUE_REFERENCES[1], 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'lesson4_dialogue_3': {'title': 'Диалог 3', 'reference_text': DIALOGUE_REFERENCES[2], 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'lesson4_dialogue_4': {'title': 'Диалог 4', 'reference_text': DIALOGUE_REFERENCES[3], 'max_duration_sec': 120.0, 'coverage_ratio_min': 0.60, 'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024},
    'neighborhood_reading': {
        'title': 'Наш район и наша улица', 'reference_text': NEIGHBORHOOD_REFERENCE_TEXT,
        'max_duration_sec': None, 'coverage_ratio_min': 0.60,
        'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024,
    },
    'lesson4_university': {
        'title': 'Мой университет — часть 1', 'reference_text': LESSON4_UNIVERSITY_REFERENCE_PARTS[0],
        'max_duration_sec': None, 'coverage_ratio_min': 0.60,
        'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024,
    },
    'lesson4_university_part2': {
        'title': 'Мой университет — часть 2', 'reference_text': LESSON4_UNIVERSITY_REFERENCE_PARTS[1],
        'max_duration_sec': None, 'coverage_ratio_min': 0.60,
        'sentence_endings': '.?!', 'max_audio_bytes': 20 * 1024 * 1024,
    },
    'moscow': {
        'title': 'Москва — столица', 'reference_text': MOSCOW_REFERENCE_TEXT,
        'max_duration_sec': 180.0, 'coverage_ratio_min': 0.60,
    },
    TASK_ID_PHOTO_ALBUM: {
        'title': 'Мой фотоальбом',
        'reference_text': PHOTO_ALBUM_REFERENCE_TEXT,
        'max_duration_sec': 60.0,
        'coverage_ratio_min': 0.60,
        'min_comma_pause_sec': MIN_COMMA_PAUSE_SEC,
        'max_comma_pause_sec': MAX_COMMA_PAUSE_SEC,
    },
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


def sentence_boundary_token_indices(reference_text: str, endings: str) -> list[dict[str, Any]]:
    tokens = list(re.finditer(r'\w+|[.?!]', reference_text, re.UNICODE))
    boundaries = []
    word_count = 0
    sentence_index = 0
    total_words = len(tokenize_ru(reference_text))
    for token in tokens:
        value = token.group()
        if value in endings:
            if word_count and word_count < total_words:
                boundaries.append({'after_sentence_index': sentence_index,
                                   'after_token_index': word_count - 1,
                                   'sentence_preview': reference_text[max(0, token.start()-70):token.end()],
                                   'punctuation': value})
            sentence_index += 1
        elif re.match(r'\w', value):
            word_count += 1
    return boundaries


def align_reference_with_gaps(reference_text, words):
    # A missed word must not consume the remainder of the ASR transcript.
    ref = tokenize_ru(reference_text)
    actual = [normalize_ru(word['word']) for word in words]
    aligned = [None] * len(ref)
    for match in SequenceMatcher(None, ref, actual, autojunk=False).get_matching_blocks():
        for offset in range(match.size):
            aligned[match.a + offset] = words[match.b + offset]
    return aligned


def score_period_pauses(
    reference_text: str,
    words: list[dict[str, Any]],
    min_pause_sec: float = MIN_PAUSE_SEC,
    min_comma_pause_sec: Optional[float] = None,
    max_comma_pause_sec: Optional[float] = None,
    sentence_endings: str = '.',
) -> dict[str, Any]:
    boundaries = period_boundary_token_indices(reference_text) if sentence_endings == '.' else sentence_boundary_token_indices(reference_text, sentence_endings)
    for boundary in boundaries:
        boundary.setdefault('punctuation', '.')
    if min_comma_pause_sec is not None:
        sentence_index = 0
        token_count = 0
        for match in re.finditer(r'\w+|[.,]', reference_text, flags=re.UNICODE):
            item = match.group()
            if item == ',':
                boundaries.append({
                    'after_sentence_index': sentence_index,
                    'after_token_index': token_count - 1,
                    'sentence_preview': reference_text[max(0, match.start() - 35):match.end()],
                    'punctuation': ',',
                })
            elif item == '.':
                sentence_index += 1
            else:
                token_count += 1
        boundaries.sort(key=lambda b: b['after_token_index'])
    aligned = (align_reference_with_gaps(reference_text, words) if sentence_endings != "."
               else align_reference_to_words(reference_text, words))
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
                'punctuation': b['punctuation'],
                'after_sentence_index': b['after_sentence_index'],
                'sentence_preview': b['sentence_preview'],
                'gap_sec': None,
                'ok': False,
                'reason': 'alignment_failed',
            })
            continue

        gap = float(nxt['start']) - float(prev['end'])
        is_comma = b['punctuation'] == ','
        minimum = min_comma_pause_sec if is_comma else min_pause_sec
        maximum = max_comma_pause_sec if is_comma else None
        pause_ok = gap >= minimum and (maximum is None or gap <= maximum)
        if not pause_ok:
            all_ok = False
        details.append({
            'punctuation': b['punctuation'],
            'after_sentence_index': b['after_sentence_index'],
            'sentence_preview': b['sentence_preview'],
            'gap_sec': round(gap, 3),
            'ok': pause_ok,
            'min_pause_sec': minimum,
            'max_pause_sec': maximum,
        })

    return {'ok': all_ok, 'details': details, 'count': len(details)}


def score_reading_from_payload(
    payload: dict[str, Any],
    reference_text: str,
    max_duration_sec: Optional[float] = MAX_DURATION_SEC,
    min_pause_sec: float = MIN_PAUSE_SEC,
    coverage_ratio_min: float = COVERAGE_TOKEN_RATIO,
    min_comma_pause_sec: Optional[float] = None,
    max_comma_pause_sec: Optional[float] = None,
    recognized_override: Optional[str] = None,
    sentence_endings: str = '.',
) -> dict[str, Any]:
    recognized_raw = extract_recognized_text(payload)
    recognized = (recognized_override if recognized_override is not None else recognized_raw) or ''
    words = extract_word_timestamps(payload)
    ratio = coverage_ratio(recognized, reference_text)
    coverage_ok = ratio >= coverage_ratio_min

    duration = payload.get('duration')
    duration_ok = False
    duration_reason: Optional[str] = None
    duration_value: Optional[float] = None
    if max_duration_sec is None:
        duration_ok = True
        try:
            candidate = float(duration)
            duration_value = candidate if math.isfinite(candidate) and candidate > 0 else None
        except (TypeError, ValueError):
            pass
    elif duration is None:
        duration_reason = 'duration_missing'
    else:
        try:
            duration_value = float(duration)
            duration_ok = math.isfinite(duration_value) and 0 < duration_value <= max_duration_sec
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
        pauses = score_period_pauses(
            reference_text, words, min_pause_sec=min_pause_sec,
            min_comma_pause_sec=min_comma_pause_sec,
            max_comma_pause_sec=max_comma_pause_sec, sentence_endings=sentence_endings,
        )
        pauses_ok = bool(pauses.get('ok'))

    ok = coverage_ok and duration_ok and pauses_ok
    return {
        'ok': ok,
        'recognized': recognized_raw,
        'recognized_for_score': recognized,
        'duration': duration_value,
        'coverage': {
            'ok': coverage_ok,
            'ratio': round(ratio, 4),
            'min_ratio': coverage_ratio_min,
        },
        'duration_check': {
            'ok': duration_ok,
            'max_sec': max_duration_sec,
            'required': max_duration_sec is not None,
            'reason': duration_reason,
        },
        'pauses': pauses,
    }


READING_CORRECT_SCHEMA: dict[str, Any] = {
    'type': 'object',
    'properties': {
        'corrected_text': {
            'type': 'string',
            'description': 'Исправленная расшифровка чтения по эталону',
        },
    },
    'required': ['corrected_text'],
}


def build_reading_correct_prompt(reference_text: str) -> str:
    ref = (reference_text or '').strip()
    if len(ref) > 8000:
        ref = ref[:8000]
    return (
        'Ученик читал вслух русский учебный текст. '
        'Исправь ошибки распознавания речи по эталону: замени слова ASR на слова эталона, '
        'если они похожи по звучанию (например «этап»→«этаж», «конкретикет»→«университет», '
        '«ход»→«вход»). Не добавляй предложения, которых нет в эталоне. '
        'В corrected_text верни только исправленный текст чтения.\n\n'
        f'Эталон:\n{ref}'
    )


def extract_corrected_text(payload: dict[str, Any]) -> Optional[str]:
    llm = payload.get('_llm_output')
    if isinstance(llm, dict):
        text = llm.get('corrected_text')
        if isinstance(text, str) and text.strip():
            return text.strip()
    if isinstance(llm, str) and llm.strip():
        return llm.strip()
    return None


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

    reference_text = task['reference_text']
    try:
        payload = transcribe_audio(
            file_bytes,
            filename,
            content_type=content_type,
            language=language,
            word_timestamps=True,
            prompt=build_reading_correct_prompt(reference_text),
            json_schema=READING_CORRECT_SCHEMA,
        )
    except RuntimeError as e:
        # LLM-анализ Nexara опционален: без него всё равно считаем по сырому ASR
        logger.warning('Reading ASR with LLM correct failed (%s); fallback plain ASR', e)
        payload = transcribe_audio(
            file_bytes,
            filename,
            content_type=content_type,
            language=language,
            word_timestamps=True,
        )

    corrected = extract_corrected_text(payload)
    result = score_reading_from_payload(
        payload, task['reference_text'],
        max_duration_sec=task.get('max_duration_sec', MAX_DURATION_SEC),
        coverage_ratio_min=task.get('coverage_ratio_min', COVERAGE_TOKEN_RATIO),
        min_comma_pause_sec=task.get('min_comma_pause_sec'),
        max_comma_pause_sec=task.get('max_comma_pause_sec'),
        recognized_override=corrected,
        sentence_endings=task.get('sentence_endings', '.'),
    )
    if corrected:
        result['recognized_corrected'] = corrected
    result['task_id'] = task_id
    result['title'] = task['title']
    if task_id in ('lesson4_university', 'lesson4_university_part2', 'neighborhood_reading', 'lesson4_introduction_dialogue', 'lesson4_free_time_dialogue') or task_id.startswith('lesson4_dialogue_'):
        result['assessment_limits'] = {name: 'not_assessed' for name in ('stress', 'intonation', 'word_endings')}
    language_out = payload.get('language')
    if language_out:
        result['language'] = language_out
    return result
