# Design

## Context

См. proposal.md — Why. Сейчас `city_speaking.html` / `class_speaking.html` пишут webm через MediaRecorder и POST multipart на `${API}/v1/voice/analyze` с полями `file`, `reference`, `language`, … Сопоставление на клиенте: `normalizeRu(recognized).includes(normalizeRu(answer))`. Прогресс 3 случайных объекта из словаря `OBJECTS`. Сохранение попыток в проекте уже есть через `save_quiz_result` (story).

## Goals / Non-Goals

**Goals:**
- Перенести транскрибацию на Django + Nexara (ключ только на сервере).
- Сохранить UX трёх шагов; зачёт слова — на бэкенде (и дублировать ту же нормализацию для согласованности).
- Сохранить Attempt один раз при 3/3, по аналогии со story (`student_code` cookie, `TASK_CODE` placeholder).

**Non-Goals:**
- Хранение аудиофайлов на диске/S3.
- Оценка произношения (phoneme/scoring) сверх «слово найдено в транскрипте».
- Реальные `task_code` в HTML (плейсхолдеры).
- Перенос словаря `OBJECTS` на сервер в v1 (эталон шлёт фронт как сейчас).

## Decisions

1. **Endpoint `POST /api/speaking/check` (multipart)**  
   Поля: `file` (audio), `reference` (эталон), опционально `language=ru`. Ответ JSON: `ok`, `recognized`, опционально `duration`/`segments` из verbose_json.  
   Альтернатива оставить `/v1/voice/analyze` отвергнута — не соответствует структуре Django `api/`.

2. **Nexara вызов с сервера**  
   `httpx` POST на `https://api.nexara.ru/api/v1/audio/transcriptions` с `Authorization: Bearer ${NEXARA_API_KEY}`, multipart file + `response_format=verbose_json` (+ language если API поддерживает). Парсим text из verbose_json.

3. **Где решать «3 успеха → Attempt»**  
   Клиент ведёт `stepIndex` как сейчас. После третьего `ok` фронт вызывает `POST /api/speaking/complete` (JSON: student_code, task_code, task_id, steps[{number, reference, recognized}]) → `save_quiz_result`.  
   Альтернатива (серверная сессия) сложнее без auth-сессии ученика.  
   Альтернатива (save внутри каждого check с флагом `finalize`) тоже ок, но отдельный complete явнее и не гоняет student_code на каждый шаг обязательно — **решение: complete отдельным запросом после 3/3**, а check может не требовать student_code.

4. **Сопоставление**  
   Та же нормализация, что на фронте (ё→е, lowercase, strip punct). Зачёт если эталон входит в распознанную строку как подстрока после нормализации (как сейчас). Выполняется на бэкенде; фронт доверяет `ok`.

5. **Конфиг**  
   `NEXARA_API_KEY`, `NEXARA_BASE_URL` (default api.nexara.ru), в `.env.example`. Без ключа — 500 на check с понятной ошибкой.

6. **api-config.js**  
   Дефолт `http://127.0.0.1:8888` как у story (сейчас speaking дефолтит 8000).

## Risks / Trade-offs

- [Качество ASR / шум] → Mitigation: сохраняем возможность повтора шага; verbose_json для отладки в логах (не обязательно весь на клиент).
- [Размер webm / таймауты] → Mitigation: разумный httpx timeout (например 60–120s); ограничить размер upload в Django при необходимости.
- [Нет cookie / placeholder task_code] → Mitigation: soft-fail complete; урок всё равно «сдан» в UI.
- [Ключ Nexara утёк на фронт] → Mitigation: только server-side.

## Migration Plan

1. Добавить env key на прод, задеплоить API.
2. Выложить обновлённые HTML speaking.
3. Подставить `TASK_CODE`.
4. Rollback: откат HTML на старый `/v1/voice/analyze` или откат API unit.

## Open Questions

- Точный контракт полей multipart Nexara (имя файла/model) — уточнить по их OpenAPI при apply; при расхождении поправить клиент httpx, не меняя публичный Django-контракт для фронта.
