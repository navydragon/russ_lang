# Tasks

## 1. Backend story_check persistence

- [x] 1.1 В `api/views.py` расширить `story_check`: читать `student_code` и `task_code`, после `check_story` вызывать `save_quiz_result` с score/ok/JSON results; плейсхолдеры `REPLACE_ME_*` и пустые коды → `saved: false`. Verify: ответ JSON содержит `saved` при ручном POST без LLM-ошибки или unit/smoke вызов view.
- [x] 1.2 Ошибки/false от `save_quiz_result` не давать 5xx; логировать и отдавать `save_error`. Verify: при неизвестном student_code HTTP 200 и `saved: false`.

## 2. Frontend story lessons

- [x] 2.1 В `tasks/family_story.html`: `TASK_CODE = "REPLACE_ME_FAMILY"`, `getStudentCode()` из cookie, payload с `student_code`/`task_code`, предупреждение при `saved === false`. Verify: в коде есть константа и чтение cookie.
- [x] 2.2 То же для `tasks/room_story.html` с `REPLACE_ME_ROOM`. Verify: симметрия с family.

## 3. Validation

- [x] 3.1 `openspec validate save-story-attempts` (или `--change`) проходит без ошибок. Verify: exit code 0.
