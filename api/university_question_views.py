"""Состояние диктанта хранится в django_session, не в присланных клиентом баллах."""
import json
import logging
import re

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .university_questions import TASKS, PASSING_SCORE, choose_words, grade_answer, public_state, run_score
from .story_llm import StoryCheckResult
from .views import _persist_story_attempt


logger = logging.getLogger('api')


def _body(request):
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeError):
        return None
    return body if isinstance(body, dict) else None


def _find_session(run_id, lock=False):
    if not isinstance(run_id, str) or not re.fullmatch(r'[a-z0-9]{32}', run_id):
        return None
    query = Session.objects.filter(pk=run_id, expire_date__gt=timezone.now())
    if lock:
        query = query.select_for_update()
    session = query.first()
    if session and session.get_decoded().get('ai_university_questions', {}).get('task_code') in TASKS:
        return session
    return None


def _response(run_id, run, **extra):
    if _old_lesson7_run(run):
        count = len(run['words'])
        if len(run['answers']) < count:
            return JsonResponse({'error': 'Вопросы задания обновились. Начните задание заново.', 'restart_required': True}, status=409)
        score = round(sum(item['score'] for item in run['answers']) * 100 / (count * 10))
        state = {'run_id': run_id, 'task_code': run['task_code'], 'student_code': run['student_code'],
                 'word_count': count, 'answered': count, 'current': None, 'answers': run['answers'],
                 'score': score, 'max_score': 100, 'passing_score': PASSING_SCORE,
                 'completed': True, 'ok': score >= PASSING_SCORE,
                 'saved': run.get('saved', False), 'save_error': run.get('save_error')}
    else:
        state = public_state(run_id, run)
    response = JsonResponse({**state, **extra})
    response['Cache-Control'] = 'no-store'
    return response


def _old_lesson7_run(run):
    return run['task_code'] in ('AI_7_4', 'AI_7_6') and run.get('question_version') != 2


@csrf_exempt
@require_POST
def start(request):
    body = _body(request)
    if body is None or not isinstance(body.get('task_code'), str) or body['task_code'] not in TASKS:
        return JsonResponse({'error': 'Неверный запрос задания.'}, status=400)
    student_code = body.get('student_code', '')
    if not isinstance(student_code, str) or len(student_code) > 50:
        return JsonResponse({'error': 'Неверный код ученика.'}, status=400)
    task_code = body['task_code']
    run = {'task_code': task_code, 'student_code': student_code.strip(), 'words': choose_words(task_code), 'answers': []}
    if task_code in ('AI_7_4', 'AI_7_6'):
        run['question_version'] = 2
    store = SessionStore()
    store.set_expiry(86400)
    store['ai_university_questions'] = run
    store.create()
    return _response(store.session_key, run)


@require_GET
def state(request):
    run_id = request.GET.get('run_id')
    session = _find_session(run_id)
    if not session:
        return JsonResponse({'error': 'Набор не найден или срок его действия истёк.'}, status=404)
    return _response(run_id, session.get_decoded()['ai_university_questions'])


@csrf_exempt
@require_POST
@transaction.atomic
def answer(request):
    body = _body(request)
    if body is None:
        return JsonResponse({'error': 'Неверный запрос.'}, status=400)
    run_id = body.get('run_id')
    session = _find_session(run_id, lock=True)
    if not session:
        return JsonResponse({'error': 'Набор не найден или срок его действия истёк.'}, status=404)
    data = session.get_decoded()
    run = data['ai_university_questions']
    if _old_lesson7_run(run):
        if len(run['answers']) == len(run['words']):
            return _response(run_id, run)
        return JsonResponse({'error': 'Вопросы задания обновились. Начните задание заново.', 'restart_required': True}, status=409)
    task_code = run['task_code']
    word_count = TASKS[task_code]['count']
    index = body.get('index')
    text = body.get('answer')
    if type(index) is not int or not isinstance(text, str) or len(text) > 500:
        return JsonResponse({'error': 'Неверный ответ.'}, status=400)
    text = text.strip()
    if 0 <= index < len(run['answers']):
        if run['answers'][index]['answer'] == text:
            return _response(run_id, run, feedback=run['answers'][index])
        return JsonResponse({'error': 'Этот ответ уже оценён; менять его нельзя.'}, status=409)
    if index != len(run['answers']) or index >= word_count:
        return JsonResponse({'error': 'Отвечайте по порядку.'}, status=409)
    try:
        result = grade_answer(run['words'][index], text, task_code)
    except Exception as exc:
        logger.warning('Question checker unavailable (%s)', type(exc).__name__)
        return JsonResponse({'error': 'ИИ-проверка недоступна. Ответ не засчитан; попробуйте отправить его ещё раз.'}, status=502)
    run['answers'].append(result)
    if len(run['answers']) == word_count:
        score = run_score(run)
        passed = score >= PASSING_SCORE
        summary = StoryCheckResult(
            ok=passed, score=score, normalized='\n'.join(a['answer'] for a in run['answers']),
            feedback='Зачёт.' if passed else 'Незачёт. Попробуйте ещё раз.',
            errors=[], recommendations=[], quality_notes=(
                f'Каждый ответ: 5 баллов за содержание и 5 за написание. '
                f'Итог: {word_count} ответов приведены к шкале 0–100.'),
        )
        run['saved'], run['save_error'] = _persist_story_attempt(
            run['student_code'], task_code, summary.normalized, summary,
            source='university_questions_check', extra_result={'run_id': run_id, 'answers': run['answers']},
        )
    session.session_data = SessionStore().encode(data)
    session.save(update_fields=['session_data'])
    return _response(run_id, run, feedback=result)
