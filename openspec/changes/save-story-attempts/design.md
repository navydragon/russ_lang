# Design

## Context

См. proposal.md — Why. Сейчас `story_check` только вызывает `check_story` и отдаёт JSON. Сохранение попыток уже централизовано в `save_quiz_result` (iSpring + email-forwarder). Cookie `student_code` уже шарится между `edu.emiit.ru` и `course.emiit.ru`.

## Goals / Non-Goals

**Goals:**
- Один round-trip: check + optional persist в `story_check`.
- Переиспользовать `save_quiz_result` без отдельного фронтового вызова `/api/quiz_result`.
- Идентификация через явный `student_code` (без base64-decode токена).

**Non-Goals:**
- Выставление cookie на LMS.
- Реальные значения `task_code` в HTML (плейсхолдеры).
- Миграции схемы БД / новый endpoint.

## Decisions

1. **Persist внутри `story_check`, не отдельный POST**  
   После `check_story` собираем `parsed_data` и вызываем `save_quiz_result`. Альтернатива (два запроса с фронта) отвергнута: больше гонок и дублирования контракта.

2. **`student_code` в body, не только cookie на бэке**  
   API часто на другом origin; браузер не обязан слать cookie LMS на API. Фронт читает cookie и кладёт код в JSON. Альтернатива ( Domains / CORS credentials ) сложнее и хрупче.

3. **Плейсхолдеры `REPLACE_ME_FAMILY` / `REPLACE_ME_ROOM`**  
   Бэкенд считает их незаполненными (`saved: false`), чтобы случайно не искать несуществующий Task.

4. **`results_content` = JSON AI-результата**  
   Единый TextField `results`; для iSpring там XML/HTML. Для story — JSON (text, score, ok, feedback, errors, …). UI отчётов покажет как текст/не-XML.

5. **Ошибка save не ломает check**  
   try/except / false от `save_quiz_result` → поля `saved`, `save_error` в JSON, HTTP 200 при успешном LLM.

## Risks / Trade-offs

- [Плейсхолдер забыли заменить] → Mitigation: явная проверка префикса `REPLACE_ME_` + UI warning.
- [Нет cookie на origin урока] → Mitigation: check работает, `saved: false`.
- [JSON в `results` не парсится quiz_report_tags] → Mitigation: тег уже fallback на plain text; приемлемо для v1.

## Migration Plan

1. Задеплоить API и HTML.
2. Подставить реальные `TASK_CODE` в HTML.
3. Rollback: откат `story_check`/HTML; данные попыток остаются в БД.
