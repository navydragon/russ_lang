# Proposal

## Why

Учителю нужен контроль чтения текста «Наш университет» (урок 3): запись голоса, полнота чтения, лимит 3 минуты и паузы после точки. Текущие задания speaking проверяют только совпадение короткого слова с транскриптом; story — письменный текст. Отдельного чтения вслух с оценкой пауз нет, а раздача `tasks/` не поддерживает подпапки уроков.

## What Changes

- Добавить папку `tasks/lesson3/` с HTML-заданием чтения «Наш университет» (запись аудио, таймер, эталонный текст, результат проверки).
- Расширить раздачу статики `tasks/`, чтобы отдавать файлы из вложенных каталогов (например `/tasks/lesson3/university_reading.html`).
- Добавить API проверки чтения на базе Nexara: покрытие эталона, `duration ≤ 180` с, паузы после точки по word timestamps.
- Сохранять успешную попытку по той же модели, что speaking (`student_code` / `task_code` / `TaskAttempt`).
- **Не** оценивать ударение и интонацию перечисления в этой change.

## Capabilities

### New Capabilities

- `task-pages`: HTTP-раздача HTML/JS/CSS из `tasks/`, включая безопасные вложенные пути для уроков.
- `reading-aloud`: контроль чтения эталонного текста вслух (ASR Nexara, покрытие, лимит времени, паузы после точки) и UI задания урока 3.

### Modified Capabilities

- (нет — в `openspec/specs/` пока нет capabilities)

## Impact

- Frontend: новый `tasks/lesson3/university_reading.html` (оболочка как у speaking/story), путь к `../api-config.js`.
- Backend: `config/task_pages.py` (URL + path traversal guard); `api/` — новый endpoint чтения (расширение Nexara-клиента: word timestamps); persist через существующий `save_quiz_result`.
- Config/env: без новых внешних вендоров; Nexara уже в проекте.
- Зависимости: без Parselmouth/ffmpeg в v1 (паузы только по Nexara word timestamps).
