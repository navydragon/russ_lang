# Proposal

## Why

AI-проверка рассказов (`/api/story/check`) сейчас только возвращает оценку в UI и не создаёт `TaskAttempt`. Нужно сохранять каждую успешную HTTP-проверку в ту же модель попыток, что и iSpring, идентифицируя студента по cookie `student_code`.

## What Changes

- Расширить `POST /api/story/check`: принимать `student_code` и `task_code`, после LLM-проверки вызывать `save_quiz_result`.
- Ответ check дополнить флагами `saved` / `save_error`; сбой сохранения не должен давать 5xx, если проверка прошла.
- В `family_story.html` / `room_story.html`: читать cookie `student_code`, слать `task_code` (плейсхолдер) вместе с `task_id` и текстом; мягкое предупреждение, если попытка не сохранена.

## Capabilities

### New Capabilities
- `story-attempt-persistence`: сохранение результата AI-проверки рассказа как попытки задания (`TaskAttempt`) по коду студента и коду задания.

### Modified Capabilities

## Impact

- Backend: `api/views.py` (`story_check`), использование `courses.services.save_quiz_result`.
- Frontend: `tasks/family_story.html`, `tasks/room_story.html`.
- Данные: записи в `courses_task_attempt` / при `ok` — `courses_student_task`.
- Зависимости LMS: cookie `student_code` на `.emiit.ru` (уже выставляется вне этого change).
