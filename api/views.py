import json
import logging
from decimal import Decimal
from typing import Optional, Tuple

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from courses.services import parse_ispring_post, save_quiz_result
from .reading_check import READING_TASKS, check_reading_audio
from .speaking_nexara import check_speaking_audio
from .story_llm import VALID_TASK_IDS, check_story

logger = logging.getLogger('api')

_TASK_CODE_PLACEHOLDER_PREFIX = 'REPLACE_ME_'


def _is_usable_task_code(task_code: str) -> bool:
    return bool(task_code) and not task_code.startswith(_TASK_CODE_PLACEHOLDER_PREFIX)


def _persist_story_attempt(
    student_code: str,
    task_code: str,
    text: str,
    result,
) -> Tuple[bool, Optional[str]]:
    """Save AI check as TaskAttempt. Returns (saved, save_error)."""
    if not student_code:
        return False, 'student_code is required'
    if not _is_usable_task_code(task_code):
        return False, 'task_code is missing or still a placeholder'

    payload = result.model_dump()
    results_content = json.dumps(
        {
            'source': 'story_check',
            'text': text,
            'ok': payload.get('ok'),
            'score': payload.get('score'),
            'feedback': payload.get('feedback'),
            'normalized': payload.get('normalized'),
            'errors': payload.get('errors'),
            'quality_notes': payload.get('quality_notes'),
            'recommendations': payload.get('recommendations'),
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

    results_content = json.dumps(
        {
            'source': 'reading_complete',
            'task_id': task_id,
            'ok': True,
            'score': 100,
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
        'score_value': Decimal(100),
        'score_percent': Decimal(100),
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
        return JsonResponse({'error': 'Transcription request failed'}, status=502)

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
