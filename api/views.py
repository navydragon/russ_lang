import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from courses.services import parse_ispring_post, save_quiz_result
from .reading_check import READING_TASKS, check_reading_audio
from .retelling_check import check_retelling_audio, MAX_AUDIO_BYTES, RETELLING_TASKS
from .audio_duration import AudioDurationError
from .speaking_nexara import check_speaking_audio, transcribe_audio, extract_recognized_text
from .story_llm import VALID_TASK_IDS, StoryCheckResult, check_story
from .excursion import score_selection, words_and_targets

logger = logging.getLogger('api')

_TASK_CODE_PLACEHOLDER_PREFIX = 'REPLACE_ME_'


def _is_usable_task_code(task_code: str) -> bool:
    return bool(task_code) and not task_code.startswith(_TASK_CODE_PLACEHOLDER_PREFIX)


def _persist_story_attempt(
    student_code: str,
    task_code: str,
    text: str,
    result,
    *, source='story_check', extra_result=None,
) -> Tuple[bool, Optional[str]]:
    """Save AI check as TaskAttempt. Returns (saved, save_error)."""
    if not student_code:
        return False, 'student_code is required'
    if not _is_usable_task_code(task_code):
        return False, 'task_code is missing or still a placeholder'

    payload = result.model_dump()
    results_content = json.dumps(
        {
            'source': source,
            'text': text,
            'ok': payload.get('ok'),
            'score': payload.get('score'),
            'feedback': payload.get('feedback'),
            'normalized': payload.get('normalized'),
            'errors': payload.get('errors'),
            'quality_notes': payload.get('quality_notes'),
            'recommendations': payload.get('recommendations'),
            **({'speech_assessment': extra_result} if extra_result is not None else {}),
        },
        ensure_ascii=False,
    )
    score = Decimal(payload.get('score') or 0)
    parsed_data = {
        'sid': student_code,
        'user_id': student_code,
        'task_code': task_code,
        'date': timezone.now(),
        'score_value': score,
        'score_percent': score,
        'result': bool(payload.get('ok')),
        'results_content': results_content,
    }
    try:
        saved = save_quiz_result(parsed_data)
    except Exception as e:
        logger.exception('Story attempt save failed: %s', e)
        return False, 'save_quiz_result raised an exception'
    if not saved:
        return False, 'save_quiz_result returned false'
    return True, None


@csrf_exempt
@require_POST
def quiz_result(request):
    try:
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        content_type = request.META.get('CONTENT_TYPE', '')

        logger.info(
            '=== Quiz result received: ip=%s content_type=%s ===',
            client_ip,
            content_type,
        )

        for key, values in request.POST.lists():
            for value in values:
                logger.info('%s = %s', key, value)

        parsed_data = parse_ispring_post(request.POST)
        if not save_quiz_result(parsed_data):
            logger.warning(
                'Не удалось сохранить результат квиза: student_code=%s, task_code=%s',
                parsed_data.get('sid'),
                parsed_data.get('task_code'),
            )

        return HttpResponse('OK', content_type='text/plain')
    except Exception as e:
        logger.exception('Ошибка обработки quiz result: %s', e)
        return HttpResponse(f'Error: {e}', content_type='text/plain', status=500)


@csrf_exempt
@require_POST
def story_check(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    task_id = (body.get('task_id') or '').strip()
    text = (body.get('text') or '').strip()
    student_code = (body.get('student_code') or '').strip()
    task_code = (body.get('task_code') or '').strip()

    if task_id not in VALID_TASK_IDS:
        return JsonResponse(
            {'error': f'Invalid task_id. Expected one of: {", ".join(sorted(VALID_TASK_IDS))}'},
            status=400,
        )

    story_task_codes = {
        'lesson7_fairytale_verbs': 'AI_7_10', 'lesson7_faculty_writing': 'AI_7_12',
        'lesson5_classroom_questions': 'AI_5_6',
    }
    if task_id in story_task_codes and task_code != story_task_codes[task_id]:
        return JsonResponse({'error': 'Неверный код задания.'}, status=400)

    if not text:
        return JsonResponse({'error': 'Text is required'}, status=400)

    try:
        result = check_story(task_id, text)
    except RuntimeError as e:
        logger.error('Story check config error: %s', e)
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.exception('Story check LLM error: %s', e)
        return JsonResponse({'error': 'LLM request failed'}, status=502)

    response = result.model_dump()
    saved, save_error = _persist_story_attempt(student_code, task_code, text, result)
    response['saved'] = saved
    if save_error:
        response['save_error'] = save_error
        logger.warning(
            'Story check not persisted: student_code=%s task_code=%s reason=%s',
            student_code or '(empty)',
            task_code or '(empty)',
            save_error,
        )
    return JsonResponse(response)


@csrf_exempt
@require_POST
def retelling_check(request):
    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'error': 'Audio file is required'}, status=400)
    if upload.size > MAX_AUDIO_BYTES:
        return JsonResponse({'error': 'Максимальный размер записи — 20 МБ.'}, status=413)
    task_id = request.POST.get('task_id', '').strip()
    task_code = request.POST.get('task_code', '').strip()
    if task_id not in RETELLING_TASKS or task_code != RETELLING_TASKS[task_id]:
        return JsonResponse({'error': 'Неверный код задания пересказа.'}, status=400)
    try:
        result, speech = check_retelling_audio(
            upload.read(), getattr(upload, 'name', 'record.webm'),
            getattr(upload, 'content_type', 'audio/webm'),
            task_id=task_id,
        )
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except AudioDurationError as exc:
        return JsonResponse({'error': str(exc)}, status=502)
    except RuntimeError:
        logger.exception('Retelling service unavailable')
        return JsonResponse({'error': 'Сервис проверки недоступен. Проверьте настройки ASR и LLM.'}, status=502)
    except Exception:
        logger.exception('Retelling check failed')
        return JsonResponse({'error': 'Не удалось проверить пересказ. Попробуйте ещё раз.'}, status=502)
    student_code = request.POST.get('student_code', '').strip()
    saved, save_error = _persist_story_attempt(
        student_code, task_code, speech['recognized'], result,
        source='retelling_check', extra_result=speech,
    )
    response = {**result.model_dump(), **speech, 'saved': saved}
    if save_error:
        response['save_error'] = save_error
    return JsonResponse(response)


@csrf_exempt
@require_POST
def picture_question_check(request):
    """Check one written or spoken question-answer pair for the lesson-five pictures."""
    task_id = request.POST.get('task_id', '').strip()
    task_code = request.POST.get('task_code', '').strip()
    mode = request.POST.get('mode', '').strip()
    picture_index = request.POST.get('picture_index', '').strip()
    if task_id != 'lesson5_classroom_questions' or task_code != 'AI_5_6':
        return JsonResponse({'error': 'Неверный код задания.'}, status=400)
    picture_data = {
        '1': ('стакан с водой стоит на столе', 'стакан, вода, стол'),
        '2': ('кошка сидит на диване', 'кошка, диван, сидеть'),
        '3': ('мальчик спит в кровати', 'мальчик, кровать, спать'),
    }
    if picture_index not in picture_data:
        return JsonResponse({'error': 'Неизвестная картинка.'}, status=400)

    image_description, support_words = picture_data[picture_index]
    if mode == 'written':
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        if not question or not answer:
            return JsonResponse({'error': 'Заполните вопрос и ответ.'}, status=400)
        student_text = f'Вопрос ученика: {question}\nОтвет ученика: {answer}'
        recognized = ''
    elif mode == 'oral':
        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'error': 'Запишите вопрос и ответ.'}, status=400)
        if upload.size > MAX_AUDIO_BYTES:
            return JsonResponse({'error': 'Максимальный размер записи — 20 МБ.'}, status=413)
        try:
            payload = transcribe_audio(
                upload.read(), getattr(upload, 'name', 'question-answer.webm'),
                content_type=getattr(upload, 'content_type', 'audio/webm'), language='ru',
            )
            recognized = extract_recognized_text(payload)
        except Exception:
            logger.exception('Picture question ASR failed')
            return JsonResponse({'error': 'Не удалось распознать запись. Попробуйте ещё раз.'}, status=502)
        if not recognized:
            return JsonResponse({'error': 'Речь не распознана. Запишите вопрос и ответ ещё раз.'}, status=400)
        student_text = 'Ученик сначала произносит вопрос, затем свой ответ. Транскрипт: ' + recognized
    else:
        return JsonResponse({'error': 'Неизвестный режим ответа.'}, status=400)

    rubric_context = (
        f'Картинка {picture_index}: {image_description}. Опорные слова: {support_words}.\n'
        + student_text
    )
    try:
        result = check_story(task_id, rubric_context)
    except RuntimeError as exc:
        logger.error('Picture question checker config error: %s', exc)
        return JsonResponse({'error': str(exc)}, status=500)
    except Exception:
        logger.exception('Picture question LLM check failed')
        return JsonResponse({'error': 'Не удалось проверить пару вопрос–ответ.'}, status=502)

    student_code = request.POST.get('student_code', '').strip()
    saved, save_error = _persist_story_attempt(
        student_code, task_code, rubric_context, result,
        source='picture_question_check',
        extra_result={'mode': mode, 'picture_index': int(picture_index), 'recognized': recognized or None},
    )
    response = result.model_dump()
    response.update({'saved': saved, 'mode': mode, 'picture_index': int(picture_index)})
    if recognized:
        response['recognized'] = recognized
    if save_error:
        response['save_error'] = save_error
    return JsonResponse(response)


def _persist_speaking_attempt(
    student_code: str,
    task_code: str,
    task_id: str,
    steps: list,
) -> Tuple[bool, Optional[str]]:
    if not student_code:
        return False, 'student_code is required'
    if not _is_usable_task_code(task_code):
        return False, 'task_code is missing or still a placeholder'
    if not isinstance(steps, list) or len(steps) < 3:
        return False, 'steps must contain at least 3 successful items'

    results_content = json.dumps(
        {
            'source': 'speaking_complete',
            'task_id': task_id,
            'steps': steps,
            'ok': True,
            'score': 100,
        },
        ensure_ascii=False,
    )
    parsed_data = {
        'sid': student_code,
        'user_id': student_code,
        'task_code': task_code,
        'date': timezone.now(),
        'score_value': Decimal(100),
        'score_percent': Decimal(100),
        'result': True,
        'results_content': results_content,
    }
    try:
        saved = save_quiz_result(parsed_data)
    except Exception as e:
        logger.exception('Speaking attempt save failed: %s', e)
        return False, 'save_quiz_result raised an exception'
    if not saved:
        return False, 'save_quiz_result returned false'
    return True, None


@csrf_exempt
@require_POST
def speaking_check(request):
    upload = request.FILES.get('file')
    reference = (request.POST.get('reference') or '').strip()
    language = (request.POST.get('language') or 'ru').strip() or 'ru'

    if not upload:
        return JsonResponse({'error': 'Audio file is required'}, status=400)
    if not reference:
        return JsonResponse({'error': 'reference is required'}, status=400)

    if upload.size > MAX_AUDIO_BYTES:
        return JsonResponse({'error': 'Максимальный размер записи — 20 МБ.'}, status=413)

    file_bytes = upload.read()
    if not file_bytes:
        return JsonResponse({'error': 'Audio file is empty'}, status=400)

    try:
        result = check_speaking_audio(
            file_bytes=file_bytes,
            filename=getattr(upload, 'name', None) or 'audio.webm',
            reference=reference,
            content_type=getattr(upload, 'content_type', None) or 'application/octet-stream',
            language=language,
        )
    except RuntimeError as e:
        logger.error('Speaking check config/ASR error: %s', e)
        msg = str(e)
        status = 500 if 'NEXARA_API_KEY' in msg else 502
        return JsonResponse({'error': msg}, status=status)
    except Exception as e:
        logger.exception('Speaking check failed: %s', e)
        return JsonResponse({'error': 'Transcription request failed'}, status=502)

    return JsonResponse(result)


@csrf_exempt
@require_POST
def speaking_complete(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    student_code = (body.get('student_code') or '').strip()
    task_code = (body.get('task_code') or '').strip()
    task_id = (body.get('task_id') or '').strip()
    steps = body.get('steps') or []

    saved, save_error = _persist_speaking_attempt(student_code, task_code, task_id, steps)
    response = {'saved': saved, 'ok': True}
    if save_error:
        response['save_error'] = save_error
        logger.warning(
            'Speaking complete not persisted: student_code=%s task_code=%s reason=%s',
            student_code or '(empty)',
            task_code or '(empty)',
            save_error,
        )
    return JsonResponse(response)


def _persist_reading_attempt(
    student_code: str,
    task_code: str,
    task_id: str,
    check_result: dict,
) -> Tuple[bool, Optional[str]]:
    if not student_code:
        return False, 'student_code is required'
    if not _is_usable_task_code(task_code):
        return False, 'task_code is missing or still a placeholder'
    if not check_result.get('ok'):
        return False, 'reading check was not successful'

    try:
        score = Decimal(str(check_result.get('score', 100)))
    except (InvalidOperation, ValueError, TypeError):
        return False, 'invalid reading score'
    if not score.is_finite() or score < 60 or score > 100:
        return False, 'invalid reading score'

    results_content = json.dumps(
        {
            'source': 'reading_complete',
            'task_id': task_id,
            'ok': True,
            'score': float(score),
            'recognized': check_result.get('recognized'),
            'duration': check_result.get('duration'),
            'coverage': check_result.get('coverage'),
            'duration_check': check_result.get('duration_check'),
            'pauses': check_result.get('pauses'),
        },
        ensure_ascii=False,
    )
    parsed_data = {
        'sid': student_code,
        'user_id': student_code,
        'task_code': task_code,
        'date': timezone.now(),
        'score_value': score,
        'score_percent': score,
        'result': True,
        'results_content': results_content,
    }
    try:
        saved = save_quiz_result(parsed_data)
    except Exception as e:
        logger.exception('Reading attempt save failed: %s', e)
        return False, 'save_quiz_result raised an exception'
    if not saved:
        return False, 'save_quiz_result returned false'
    return True, None


@csrf_exempt
@require_POST
def reading_check(request):
    upload = request.FILES.get('file')
    task_id = (request.POST.get('task_id') or 'university').strip() or 'university'
    language = (request.POST.get('language') or 'ru').strip() or 'ru'

    if not upload:
        return JsonResponse({'error': 'Audio file is required'}, status=400)
    if task_id not in READING_TASKS:
        return JsonResponse(
            {'error': f'Invalid task_id. Expected one of: {", ".join(sorted(READING_TASKS))}'},
            status=400,
        )

    file_bytes = upload.read()
    if not file_bytes:
        return JsonResponse({'error': 'Audio file is empty'}, status=400)

    try:
        result = check_reading_audio(
            file_bytes=file_bytes,
            filename=getattr(upload, 'name', None) or 'audio.webm',
            task_id=task_id,
            content_type=getattr(upload, 'content_type', None) or 'application/octet-stream',
            language=language,
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except RuntimeError as e:
        logger.error('Reading check config/ASR error: %s', e)
        msg = str(e)
        status = 500 if 'NEXARA_API_KEY' in msg else 502
        return JsonResponse({'error': msg}, status=status)
    except Exception as e:
        logger.exception('Reading check failed: %s', e)
        return JsonResponse(
            {'error': 'Transcription request failed', 'detail': str(e)},
            status=502,
        )

    return JsonResponse(result)


@csrf_exempt
@require_POST
def reading_complete(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    student_code = (body.get('student_code') or '').strip()
    task_code = (body.get('task_code') or '').strip()
    task_id = (body.get('task_id') or '').strip()
    check_result = body.get('result') or {}
    if not isinstance(check_result, dict):
        check_result = {}

    reading_codes = {
        'lesson7_vdnh_reading': 'AI_7_7', 'lesson7_fairytale_reading': 'AI_7_8', 'lesson7_gagarin_reading': 'AI_7_9',
        'lesson5_classroom_reading': 'AI_5_1', 'lesson5_juan_carlos_reading': 'AI_5_2',
        'lesson5_family_reading': 'AI_5_3', 'lesson5_parrot_reading': 'AI_5_4',
        'lesson5_thomas_edward_reading': 'AI_5_5',
    }
    if task_id in reading_codes:
        if task_code != reading_codes[task_id]:
            return JsonResponse({'error': 'Неверный код задания.'}, status=400)
        try:
            score = float(check_result['score'])
            if not 0 <= score <= 100 or type(check_result.get('ok')) is not bool:
                raise ValueError()
            result = StoryCheckResult(ok=check_result['ok'], score=round(score), normalized=check_result.get('recognized', ''),
                                      feedback='Чтение проверено.', errors=[], recommendations=[], quality_notes='')
        except (KeyError, ValueError, TypeError):
            return JsonResponse({'error': 'Некорректный результат чтения.'}, status=400)
        saved, save_error = _persist_story_attempt(student_code, task_code, result.normalized, result,
                                                  source='reading_complete', extra_result=check_result)
    else:
        saved, save_error = _persist_reading_attempt(student_code, task_code, task_id, check_result)
    response = {'saved': saved, 'ok': bool(check_result.get('ok'))}
    if save_error:
        response['save_error'] = save_error
        logger.warning(
            'Reading complete not persisted: student_code=%s task_code=%s reason=%s',
            student_code or '(empty)',
            task_code or '(empty)',
            save_error,
        )
    return JsonResponse(response)


@csrf_exempt
@require_POST
def neighborhood_verbs_check(request):
    import re
    from .reading_check import NEIGHBORHOOD_REFERENCE_TEXT
    from .story_llm import StoryCheckResult
    try:
        body = json.loads(request.body.decode('utf-8'))
        selected = body.get('selected')
        student_code = body.get('student_code', '')
        words = re.findall(r'[А-Яа-яЁё]+', NEIGHBORHOOD_REFERENCE_TEXT)
        expected = {i for i, word in enumerate(words) if word.casefold() in {'находится', 'учится', 'любит', 'говорит', 'переводит', 'находятся'}}
        if not isinstance(selected, list) or any(type(i) is not int or i < 0 or i >= len(words) for i in selected) or not isinstance(student_code, str):
            raise ValueError()
        chosen = set(selected)
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Некорректный ответ'}, status=400)
    correct = len(chosen & expected)
    wrong = len(chosen - expected)
    score = round(100 * max(0, correct - wrong) / len(expected))
    result = StoryCheckResult(ok=score >= 60, score=score, feedback=f'Найдено: {correct} из {len(expected)}. Лишних слов: {wrong}.', normalized='', errors=[], quality_notes='', recommendations=[])
    saved, error = _persist_story_attempt(student_code.strip(), 'AI_4_17', ', '.join(words[i] for i in sorted(chosen)), result, source='neighborhood_verbs_check')
    response = {**result.model_dump(), 'saved': saved, 'correct': correct, 'total': len(expected), 'wrong': wrong}
    if error: response['save_error'] = error
    return JsonResponse(response)


@csrf_exempt
@require_POST
def excursion_highlight_check(request):
    from .story_llm import StoryCheckResult
    try:
        body = json.loads(request.body.decode('utf-8'))
        if not isinstance(body, dict) or body.get('task_code') != 'AI_7_2':
            raise ValueError('Неверный код задания.')
        student_code = body.get('student_code', '')
        if not isinstance(student_code, str) or len(student_code) > 50:
            raise ValueError('Неверный код ученика.')
        result = score_selection(body.get('selected'))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return JsonResponse({'error': str(exc) or 'Некорректный ответ.'}, status=400)
    words, _ = words_and_targets()
    selected = body['selected']
    answer = json.dumps({category: [words[i] for i in indexes] for category, indexes in selected.items()}, ensure_ascii=False)
    grade = StoryCheckResult(ok=result['ok'], score=result['score'], normalized=answer,
                             feedback='Проверены формы родительного падежа множественного числа и выражения времени.',
                             errors=[], quality_notes='Каждая категория даёт до 50 баллов; лишние слова снижают балл.',
                             recommendations=[])
    saved, error = _persist_story_attempt(student_code.strip(), 'AI_7_2', answer, grade,
                                          source='excursion_highlight_check', extra_result=result)
    response = {**result, 'saved': saved}
    if error:
        response['save_error'] = error
    return JsonResponse(response)
