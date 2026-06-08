import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from courses.services import parse_ispring_post, save_quiz_result

logger = logging.getLogger('api')


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
