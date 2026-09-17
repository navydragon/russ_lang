from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache

import httpx
from django.conf import settings
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

logger = logging.getLogger('api')

VALID_TASK_IDS = frozenset({'family', 'room'})

SYSTEM_PROMPT = """\
Ты — преподаватель русского языка для иностранных студентов.
Проверяешь короткий письменный рассказ ученика.

Перед финальным ответом ОБЯЗАТЕЛЬНО вызови инструменты:
1. check_sentence_rubric — точное число предложений и выполнение рубрики.
2. check_vocab_rubric — какие слова темы найдены и выполнена ли лексическая рубрика.

Для completeness (мало предложений / мало слов темы) опирайся ТОЛЬКО на результаты инструментов, не считай сам.

Проверь:
1. Грамматику и орфографию (ошибки с точными позициями в тексте).
2. Выполнение рубрики — по результатам инструментов.
3. Связность и качество текста (логика, последовательность, уместность).

Правила для поля normalized:
- Верни текст ученика с минимальными правками (пробелы, явные опечатки).
- Длина normalized должна совпадать с исходным текстом по смыслу подсветки.
- Если правок нет — normalized = исходный текст.

Правила для errors:
- start и end — индексы символов в normalized (0-based, end exclusive).
- code: grammar | completeness | coherence | quality
- message — короткое объяснение на русском для ученика.
- completeness по предложениям — только если check_sentence_rubric.ok = false.
- completeness по лексике — только если check_vocab_rubric.ok = false.
- Если check_vocab_rubric.ok = true: ЗАПРЕЩЕНО errors про недостающих родственников/слова темы.
  Неупомянутые слова из optional_words инструмента — только в recommendations.

Поле recommendations — список необязательных советов (0–3 пункта).
Используй optional_words из check_vocab_rubric, когда лексика выполнена.
Не дублируй recommendations в errors.

Правила для ok:
- ok=true только если нет грамматических/орфографических ошибок И оба инструмента вернули ok=true.
- Мелкие стилистические замечания не делают ok=false, если они в quality_notes.

Правила для score (0..100):
- Учитывай грамматику, рубрику (по инструментам) и качество/связность.

feedback — 1–2 предложения для ученика. Обращайся нейтрально («Вы», «Обратите внимание»).
Не выдумывай и не используй имя ученика, если оно не указано явно в тексте задания или в данных.
quality_notes — 1–3 предложения о связности и качестве рассказа (без требований дополнительной лексики, если vocab ok).
"""


@dataclass(frozen=True)
class TaskConfig:
    title: str
    min_sentences: int
    min_vocab_hits: int
    vocab: tuple[str, ...]


TASK_CONFIGS: dict[str, TaskConfig] = {
    'family': TaskConfig(
        title='Рассказ «Семья»',
        min_sentences=3,
        min_vocab_hits=3,
        vocab=(
            'мама', 'папа', 'брат', 'сестра', 'бабушка', 'дедушка',
            'сын', 'дочь', 'дядя', 'тётя',
        ),
    ),
    'room': TaskConfig(
        title='Рассказ «Комната»',
        min_sentences=3,
        min_vocab_hits=3,
        vocab=(
            'комната', 'стол', 'стул', 'кресло', 'диван', 'телевизор',
            'пол', 'ковёр', 'чемодан', 'стена', 'картина', 'радио',
            'полка', 'кровать', 'подушка', 'одеяло', 'ванная', 'зеркало',
            'полотенце', 'шкаф', 'костюм', 'рубашка', 'платье', 'пальто', 'шапка',
        ),
    ),
}


class StoryError(BaseModel):
    start: int
    end: int
    code: str = Field(description='grammar | completeness | coherence | quality')
    message: str


class StoryCheckResult(BaseModel):
    ok: bool
    score: int = Field(ge=0, le=100)
    feedback: str
    normalized: str
    errors: list[StoryError] = Field(default_factory=list)
    quality_notes: str
    recommendations: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class StoryDeps:
    task_id: str
    text: str


class SentenceRubricResult(BaseModel):
    sentence_count: int
    min_sentences: int
    ok: bool
    message: str


class VocabRubricResult(BaseModel):
    hit_words: list[str]
    min_vocab_hits: int
    ok: bool
    optional_words: list[str] = Field(
        description='Слова темы, не упомянутые в тексте — только для recommendations, не errors',
    )
    message: str


def _vocab_hit_words(text: str, vocab: tuple[str, ...]) -> list[str]:
    text_lower = text.lower().replace('ё', 'е')
    return [w for w in vocab if w.lower().replace('ё', 'е') in text_lower]


def _vocab_hits(text: str, vocab: tuple[str, ...]) -> int:
    return len(_vocab_hit_words(text, vocab))


def _count_sentences(text: str) -> int:
    parts = re.split(r'[.!?…]+', text)
    return sum(1 for p in parts if p.strip())


def check_sentence_rubric(ctx: RunContext[StoryDeps]) -> SentenceRubricResult:
    """Подсчитать предложения в тексте ученика и проверить рубрику по количеству предложений."""
    cfg = TASK_CONFIGS[ctx.deps.task_id]
    count = _count_sentences(ctx.deps.text)
    ok = count >= cfg.min_sentences
    if ok:
        message = f'Найдено {count} предложений, нужно минимум {cfg.min_sentences}. Рубрика выполнена.'
    else:
        message = f'Найдено {count} предложений, нужно минимум {cfg.min_sentences}. Рубрика не выполнена.'
    logger.info('Tool check_sentence_rubric: count=%d ok=%s', count, ok)
    return SentenceRubricResult(
        sentence_count=count,
        min_sentences=cfg.min_sentences,
        ok=ok,
        message=message,
    )


def check_vocab_rubric(ctx: RunContext[StoryDeps]) -> VocabRubricResult:
    """Проверить слова темы в тексте. Достаточно любых N слов из списка, не всех."""
    cfg = TASK_CONFIGS[ctx.deps.task_id]
    hit_words = _vocab_hit_words(ctx.deps.text, cfg.vocab)
    optional_words = [w for w in cfg.vocab if w not in hit_words]
    ok = len(hit_words) >= cfg.min_vocab_hits
    if ok:
        message = (
            f'Найдены слова темы: {", ".join(hit_words)} '
            f'({len(hit_words)} из {cfg.min_vocab_hits}). Рубрика выполнена.'
        )
    else:
        message = (
            f'Найдены слова темы: {", ".join(hit_words) if hit_words else "нет"} '
            f'({len(hit_words)} из {cfg.min_vocab_hits}). Рубрика не выполнена.'
        )
    logger.info('Tool check_vocab_rubric: hits=%s ok=%s', hit_words, ok)
    return VocabRubricResult(
        hit_words=hit_words,
        min_vocab_hits=cfg.min_vocab_hits,
        ok=ok,
        optional_words=optional_words,
        message=message,
    )


def _build_user_prompt(task_id: str, text: str) -> str:
    cfg = TASK_CONFIGS[task_id]
    vocab_list = ', '.join(cfg.vocab)
    return (
        f'Задание: {cfg.title}\n'
        f'Рубрика:\n'
        f'- минимум {cfg.min_sentences} предложений\n'
        f'- минимум {cfg.min_vocab_hits} слов из темы (любые из списка): {vocab_list}\n\n'
        f'Сначала вызови check_sentence_rubric и check_vocab_rubric, затем верни финальный результат.\n\n'
        f'Текст ученика:\n{text}'
    )


def _is_optional_vocab_nag(message: str, vocab: tuple[str, ...]) -> bool:
    msg = message.lower().replace('ё', 'е')
    if 'предложен' in msg and not any(p in msg for p in ('нет слов', 'не содержит', 'не упомян')):
        return False
    nag_phrases = (
        'нет слов', 'не содержит', 'не упомянут', 'не упомина', 'но нет',
        'отсутств', 'обязательн', 'из темы', 'лексик', 'родственник',
    )
    if any(p in msg for p in nag_phrases):
        return True
    listed = sum(1 for w in vocab if w.lower().replace('ё', 'е') in msg)
    return listed >= 2


def _merge_recommendations(
    llm_recs: list[str],
    text: str,
    cfg: TaskConfig,
    lexicon_ok: bool,
) -> list[str]:
    recs = [r.strip() for r in llm_recs if r and r.strip()]
    if not lexicon_ok:
        return recs[:3]

    missing = [w for w in cfg.vocab if w not in _vocab_hit_words(text, cfg.vocab)]
    if missing:
        hint = (
            f'Задание по лексике выполнено. По желанию можно добавить: '
            f'{", ".join(missing[:5])}.'
        )
        if not any('по желанию' in r.lower() or 'можно добавить' in r.lower() for r in recs):
            recs.append(hint)
    return recs[:3]


def _sanitize_result(result: StoryCheckResult, original_text: str, task_id: str) -> StoryCheckResult:
    normalized = result.normalized.strip() if result.normalized.strip() else original_text
    text_len = len(normalized)

    clean_errors: list[StoryError] = []
    for err in result.errors:
        if not (0 <= err.start < err.end <= text_len):
            logger.warning('Dropped invalid span: %s', err)
            continue
        clean_errors.append(err)

    cfg = TASK_CONFIGS[task_id]
    sentence_count = _count_sentences(normalized)
    hits = _vocab_hits(normalized, cfg.vocab)
    lexicon_ok = hits >= cfg.min_vocab_hits

    if lexicon_ok:
        dropped = [
            e for e in clean_errors
            if e.code in ('completeness', 'quality', 'coherence')
            and _is_optional_vocab_nag(e.message, cfg.vocab)
        ]
        if dropped:
            logger.warning('Dropped optional-vocab nag errors: %s', dropped)
            clean_errors = [e for e in clean_errors if e not in dropped]

    if sentence_count < cfg.min_sentences:
        has_sentence_error = any(e.code == 'completeness' and 'предложен' in e.message.lower() for e in clean_errors)
        if not has_sentence_error:
            clean_errors.append(StoryError(
                start=0,
                end=text_len,
                code='completeness',
                message=f'Нужно минимум {cfg.min_sentences} предложений (найдено: {sentence_count}).',
            ))

    if hits < cfg.min_vocab_hits:
        has_vocab_error = any(
            e.code == 'completeness' and _is_optional_vocab_nag(e.message, cfg.vocab)
            for e in clean_errors
        )
        if not has_vocab_error:
            clean_errors.append(StoryError(
                start=0,
                end=text_len,
                code='completeness',
                message=(
                    f'Нужно упомянуть минимум {cfg.min_vocab_hits} слов из темы '
                    f'(найдено: {hits}).'
                ),
            ))

    grammar_errors = [e for e in clean_errors if e.code in ('grammar', 'completeness')]
    ok = len(grammar_errors) == 0 and result.ok
    score = max(0, min(100, result.score))
    recommendations = _merge_recommendations(result.recommendations, normalized, cfg, lexicon_ok)

    return StoryCheckResult(
        ok=ok,
        score=score,
        feedback=result.feedback,
        normalized=normalized,
        errors=clean_errors,
        quality_notes=result.quality_notes,
        recommendations=recommendations,
    )


@lru_cache(maxsize=1)
def _get_agent() -> Agent[StoryDeps, StoryCheckResult]:
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0))
    model = OpenAIChatModel(
        settings.LLM_MODEL,
        provider=OpenAIProvider(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            http_client=http_client,
        ),
    )
    return Agent(
        model,
        deps_type=StoryDeps,
        output_type=StoryCheckResult,
        system_prompt=SYSTEM_PROMPT,
        tools=[check_sentence_rubric, check_vocab_rubric],
    )


def check_story(task_id: str, text: str) -> StoryCheckResult:
    if task_id not in VALID_TASK_IDS:
        raise ValueError(f'Unknown task_id: {task_id}')

    if not settings.LLM_API_KEY:
        raise RuntimeError('LLM_API_KEY is not configured')

    original = text.strip()
    agent = _get_agent()
    user_prompt = _build_user_prompt(task_id, original)

    logger.info('Story check: task_id=%s text_len=%d', task_id, len(original))
    run_result = agent.run_sync(user_prompt, deps=StoryDeps(task_id=task_id, text=original))
    result = run_result.output
    return _sanitize_result(result, original, task_id)
