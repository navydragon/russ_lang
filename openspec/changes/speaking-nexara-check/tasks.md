# Tasks

## 1. Backend Nexara + speaking API

- [x] 1.1 Добавить `NEXARA_API_KEY` / `NEXARA_BASE_URL` в `config/settings.py` и `.env.example`. Verify: settings читают env, example содержит ключи-плейсхолдеры.
- [x] 1.2 Реализовать клиент транскрибации (модуль `api/`) — POST multipart на Nexara `audio/transcriptions` с `response_format=verbose_json`, извлечь текст. Verify: unit/smoke с моком httpx или ручной вызов при наличии ключа.
- [x] 1.3 Endpoint `POST /api/speaking/check`: принять file+reference, нормализовать и сопоставить, вернуть `{ok, recognized, ...}`. Verify: 400 без файла; при моке ASR — ok true/false.
- [x] 1.4 Endpoint `POST /api/speaking/complete`: после 3 успехов сохранить через `save_quiz_result` (student_code, task_code, JSON results); soft-fail `saved`/`save_error`. Verify: без кодов — saved false; плейсхолдер REPLACE_ME_ — saved false.

## 2. Frontend speaking lessons

- [x] 2.1 Обновить `tasks/city_speaking.html`: вызов `/api/speaking/check`, доверие к `ok`, после 3/3 — complete + cookie student_code + TASK_CODE placeholder. Verify: в коде нет `/v1/voice/analyze`.
- [x] 2.2 То же для `tasks/class_speaking.html`. Verify: симметрия с city.
- [x] 2.3 Выровнять дефолт API в speaking/`api-config.js` на порт Django (8888). Verify: дефолт совпадает со story.

## 3. Validation

- [x] 3.1 `openspec validate speaking-nexara-check` проходит. Verify: exit code 0.
