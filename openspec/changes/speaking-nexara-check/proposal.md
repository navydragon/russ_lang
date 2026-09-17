# Proposal

## Why

Уроки говорения (`city_speaking.html`, `class_speaking.html`) сейчас шлют аудио на внешний `/v1/voice/analyze` (порт 8000), которого нет в этом Django-проекте. Нужна проверка на бэкенде через транскрибацию Nexara и сохранение `TaskAttempt` только после трёх успешных слов — по той же модели идентификации, что и story.

## What Changes

- Новый endpoint проверки говорения: multipart audio + эталонное слово; бэкенд вызывает Nexara `POST https://api.nexara.ru/api/v1/audio/transcriptions` с `response_format=verbose_json`.
- Ответ API: распознанный текст, признак совпадения с эталоном, служебные поля транскрипта (по возможности из verbose_json).
- Фронт speaking-уроков переключается на Django API (`apiBaseUrl` + новый путь), сохраняет клиентскую логику 3 шагов.
- После третьего успешного слова — запись попытки через `save_quiz_result` (cookie `student_code`, `task_code` с плейсхолдером), soft-fail как у story.
- Конфиг: `NEXARA_API_KEY` (и при необходимости base URL) в settings / `.env.example`.

## Capabilities

### New Capabilities
- `speaking-check`: транскрибация аудио через Nexara, сопоставление с эталонным словом, ответ фронту и условное сохранение попытки после трёх успехов.

### Modified Capabilities

## Impact

- Backend: новый view/модуль в `api/`, URL в `api/urls.py`, settings/env.
- Frontend: `tasks/city_speaking.html`, `tasks/class_speaking.html`, `tasks/api-config.js` (дефолтный порт).
- Данные: `TaskAttempt` / `StudentTask` при завершении урока (3/3).
- Внешний сервис: Nexara transcription API (ключ на сервере, не на фронте).
