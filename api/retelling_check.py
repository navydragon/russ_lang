"""Устный пересказ: ASR и проверка содержания, без имитации оценки ударения."""
from .speaking_nexara import transcribe_audio, extract_recognized_text
from .story_llm import check_story
from .audio_duration import measure_audio_duration


TASK_ID = 'university_retelling'
RETELLING_TASKS = {
    'university_retelling': 'AI_3_2',
    'moscow_retelling': 'AI_3_6',
    'novgorod_retelling': 'AI_3_11',
    'vdnh_retelling': 'AI_7_1',
    'lesson7_fairytale_retelling': 'AI_7_11',
}
MAX_AUDIO_BYTES = 20 * 1024 * 1024


def check_retelling_audio(file_bytes, filename, content_type='audio/webm', *, task_id=TASK_ID):
    if task_id not in RETELLING_TASKS:
        raise ValueError('Неизвестное задание пересказа.')
    if not file_bytes:
        raise ValueError('Аудиозапись пуста.')
    if len(file_bytes) > MAX_AUDIO_BYTES:
        raise ValueError('Аудиозапись слишком большая. Максимум — 20 МБ.')
    measured_duration = measure_audio_duration(file_bytes, filename)
    payload = transcribe_audio(file_bytes, filename, content_type=content_type, language='ru')
    recognized = extract_recognized_text(payload)
    if not recognized:
        raise ValueError('Речь не распознана. Запишите пересказ ещё раз.')
    result = check_story(task_id, recognized)
    return result, {
        'recognized': recognized,
        'duration': measured_duration,
        'passing_score': 60,
        'stress_check': {
            'status': 'not_assessed',
            'message': 'Ударение автоматически не проверяется: требуется отдельная оценка аудио.',
        },
    }
