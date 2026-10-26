import hashlib
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .forms import StudentForm
from .importing import MAX_SIZE, ImportError, read_rows, template_bytes
from .models import Group, Student
from .portal import PortalError
from .roster import save_student


def staff_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@sensitive_post_parameters('password')
@staff_required
@require_http_methods(['GET', 'POST'])
def student_form(request, group_id, student_id=None):
    group = get_object_or_404(Group, pk=group_id)
    student = get_object_or_404(Student, pk=student_id, group=group) if student_id else None
    form = StudentForm(request.POST if request.method == 'POST' else None, student=student)
    if request.method == 'POST' and form.is_valid():
        try:
            save_student(group.pk, form.cleaned_data, student.pk if student else None)
        except PortalError as exc:
            form.add_error(None, str(exc))
        else:
            return JsonResponse({'ok': True})
    return render(request, 'students/student_modal_form.html', {'form': form, 'group': group, 'student': student}, status=400 if request.method == 'POST' else 200)


@staff_required
@require_http_methods(['GET'])
def import_template(request, group_id):
    get_object_or_404(Group, pk=group_id)
    response = HttpResponse(template_bytes(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="students.xlsx"'
    return response


@sensitive_post_parameters()
@staff_required
@require_http_methods(['GET', 'POST'])
def import_students(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'GET':
        return render(request, 'students/import_students.html', {'group': group})
    upload = request.FILES.get('file')
    if not upload or upload.size > MAX_SIZE:
        return JsonResponse({'error': 'Выберите XLSX размером не более 5 МБ.'}, status=400)
    content = upload.read(MAX_SIZE + 1)
    try:
        rows = read_rows(content, group)
    except ImportError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    identity = {'hash': hashlib.sha256(content).hexdigest(), 'group': group.pk, 'user': request.user.pk}
    if request.POST.get('phase') != 'execute':
        safe = [{key: value for key, value in row.items() if key != 'password'} for row in rows]
        return JsonResponse({'rows': safe, 'token': signing.dumps(identity, salt='roster-import'), 'total': len(rows)})
    try:
        signed = signing.loads(request.POST.get('token', ''), salt='roster-import', max_age=1800)
        if signed != identity:
            raise signing.BadSignature
        offset = int(request.POST.get('offset', '0'))
        if offset < 0 or offset >= len(rows) or offset % 25:
            raise ValueError
    except (signing.BadSignature, ValueError):
        return JsonResponse({'error': 'Файл или подтверждение изменились. Проверьте файл заново.'}, status=400)
    results = []
    unavailable = False
    for row in rows[offset:offset + 25]:
        result = {'row_number': row['row_number'], 'code': row['code']}
        if unavailable:
            result.update(status='not_run', message='Не выполнено: портал недоступен.')
        else:
            try:
                _, status = save_student(group.pk, row)
                result.update(status=status, message={'created': 'Создано', 'updated': 'Обновлено', 'unchanged': 'Без изменений'}[status])
            except PortalError as exc:
                result.update(status='uncertain' if exc.uncertain else 'error', message=str(exc))
                unavailable = exc.uncertain or exc.code in {'configuration', '401', '403'}
        results.append(result)
    next_offset = offset + len(results)
    return JsonResponse({'results': results, 'next_offset': next_offset, 'done': unavailable or next_offset >= len(rows), 'remaining': len(rows) - next_offset})
