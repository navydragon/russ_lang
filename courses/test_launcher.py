"""Локальная страница запуска с фиксированной тестовой личностью."""
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from courses.models import Task, TaskAttempt, AssignmentReviewConfirmation
from courses.review_dates import REVIEW_CHANGE_DATES
from courses.task_catalog import TASK_CATALOG, TEST_COURSE_NAME, TEST_STUDENT_CODE
from students.models import Student


@require_GET
def test_launcher(request):
    if not settings.DEBUG:
        raise Http404

    student = Student.objects.filter(code=TEST_STUDENT_CODE).first()
    tasks = {
        task.code: task for task in Task.objects.filter(
            lesson__course__name=TEST_COURSE_NAME, code__in=[d.code for d in TASK_CATALOG],
        )
    }
    attempts = list(TaskAttempt.objects.filter(
        student=student, task__lesson__course__name=TEST_COURSE_NAME,
    ).select_related('task').order_by('-datetime', '-pk')[:20]) if student else []
    confirmations = set(AssignmentReviewConfirmation.objects.filter(confirmed=True).values_list("task_code", flat=True))
    lessons = []
    for number in sorted({definition.lesson for definition in TASK_CATALOG}):
        rows = []
        for definition in TASK_CATALOG:
            if definition.lesson != number:
                continue
            seeded = definition.code in tasks
            rows.append({
                'definition': definition, 'seeded': seeded,
                'change_date': REVIEW_CHANGE_DATES.get(definition.code),
                'confirmed': definition.code in confirmations,
                'can_launch': bool(student and seeded and definition.html_path),
            })
        lessons.append({'number': number, 'tasks': rows})

    response = render(request, 'courses/test_launcher.html', {
        'student': student, 'student_code': TEST_STUDENT_CODE,
        'lessons': lessons, 'attempts': attempts,
        'seeded_count': len(tasks), 'task_count': len(TASK_CATALOG),
    })
    response.set_cookie(
        'student_code', TEST_STUDENT_CODE, path='/',
        httponly=False, samesite='Lax', secure=request.is_secure(),
    )
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
def set_review_confirmation(request):
    if not settings.DEBUG:
        raise Http404
    code = request.POST.get('task_code', '')
    value = request.POST.get('confirmed', '')
    if code not in {item.code for item in TASK_CATALOG} or value not in ('true', 'false'):
        return JsonResponse({'error': 'Некорректные данные подтверждения.'}, status=400)
    confirmation, _ = AssignmentReviewConfirmation.objects.update_or_create(
        task_code=code, defaults={'confirmed': value == 'true'},
    )
    return JsonResponse({'confirmed': confirmation.confirmed})
