# Design

## Context

См. proposal.md — Why. Сейчас speaking (`/api/speaking/check`) сверяет короткое `reference` с транскриптом Nexara (`reference in recognized` после normalize). Story проверяет письменный текст через LLM. `config/task_pages.py` отдаёт только basename (`/tasks/<file>`), без подпапок. Nexara уже вызывается с `response_format=verbose_json`; word-level timestamps доступны через `timestamp_granularities[]=word` (документация Nexara), но текущий клиент их не запрашивает.

## Goals / Non-Goals

**Goals:**
- Вложенная раздача `tasks/lesson3/...` без path traversal.
- Endpoint чтения: coverage эталона + duration ≤ 180s + паузы после `.` по word timestamps Nexara.
- HTML UI в оболочке speaking/story; persist по образцу speaking complete.
- Эталонный текст и границы предложений — на сервере (не доверять эталон с клиента для scoring).

**Non-Goals:**
- Оценка ударения и интонации перечисления.
- Parselmouth / ffmpeg / внешний pronunciation API.
- Пиксель-в-пиксель UI со скрина стороннего курса (инструкция/глоссарий/коллаж) — опциональные картинки только если уже есть ассеты.
- Хранение аудиофайлов на диске/S3.
- Реальные `task_code` в HTML (плейсхолдер, как у speaking).

## Decisions

1. **Отдельный API, не reuse speaking/check**  
   Speaking заточен под одно короткое слово и `ok` = substring. Reading нужен полный эталон, duration gate и список пауз.  
   Решение: `POST /api/reading/check` (multipart: `file`) и `POST /api/reading/complete` (JSON).  
   Альтернатива (флаги на speaking) отвергнута — размывает контракт.

2. **Эталон на сервере**  
   Сервер хранит канонический текст «Наш университет» (и список границ предложений после `.`) для `task_id=university` / lesson3. Клиент шлёт только аудио (+ student/task meta на complete).  
   Альтернатива (reference с клиента) отвергнута — легко подменить эталон.

3. **Coverage**  
   Нормализация как в speaking (`ё→е`, lowercase, strip punct).  
   Зачёт покрытия: нормализованный эталон входит в нормализованный транскрипт **или** доля общих токенов эталона в транскрипте ≥ порога (стартовый порог **0.85** токенов эталона найдены в порядке / bag-of-words — зафиксировать простую bag-of-words: ≥ 85% токенов эталона присутствуют в recognized). Предпочтение простой реализации: **≥ 85% уникальных токенов эталона встречаются в recognized** (достаточно для foreign-learner ASR шума).  
   Альтернатива strict full-string includes — слишком хрупко на длинном абзаце.

4. **Паузы после точки**  
   Запросить у Nexara word timestamps. Сопоставить слова эталона (без пунктуации) с `words[]` по порядку (жадное выравнивание). Для каждой границы предложения (конец слова перед `.` → начало следующего предложения) измерить `next.start - prev.end`. Минимум паузы: **0.30 s** (конфиг-константа, калибруемая). Все границы с точкой в эталоне должны пройти (кроме отсутствия следующего предложения).  
   Альтернатива silence detection (Praat) — отложена (Non-Goals).

5. **Duration**  
   Использовать `duration` из verbose_json Nexara; fail если `> 180`. Если duration отсутствует — fail с явной причиной (не угадывать).

6. **Overall `ok`**  
   `ok = coverage_ok AND duration_ok AND all_period_pauses_ok`.

7. **Nested task serving**  
   URL: `^tasks/(?P<path>.+)$` с resolve + `relative_to(TASKS_DIR)` / startswith guard; суффиксы как сейчас. Корневые файлы и `lesson3/` работают одним правилом.  
   `api-config.js` в корне `tasks/`; из lesson3 подключать `../api-config.js`.

8. **UI file**  
   `tasks/lesson3/university_reading.html`: теги # ЧТЕНИЕ / говорение-запись, текст в paper, кнопки записи как speaking, сайдбар результата (recognized, duration, список пауз по предложениям). Таймер записи/предупреждение на 3 мин на клиенте + серверный hard fail.

9. **Nexara client extension**  
   Расширить `transcribe_audio` опциональным `word_timestamps=True` → form field `timestamp_granularities[]=word`. Speaking path без изменений по умолчанию.

## Risks / Trade-offs

- [ASR пропускает/переставляет слова → ложные fail coverage/пауз] → Mitigation: порог 85%; показать recognized и детали пауз; разрешить повтор записи.
- [Word timestamps не пришли] → Mitigation: `ok=false`, явная ошибка `word_timestamps_missing`, не молчать.
- [Порог 0.30s слишком строгий/мягкий] → Mitigation: одна константа в settings/модуле; калибровка после 1–2 записей без смены API-контракта.
- [Длинное webm, таймаут 120s] → Mitigation: уже есть httpx timeout; клиентский лимит 3 мин.
- [Выравнивание эталон↔words хрупко] → Mitigation: нормализация токенов; при сбое alignment — fail с причиной, не «тихий ok».

## Migration Plan

1. Задеплоить `task_pages` + API reading + HTML lesson3.
2. Подставить реальный `TASK_CODE` в HTML при интеграции с курсом.
3. Rollback: убрать URL reading / вернуть старый task_pages regex; HTML в подпапке просто перестанет открываться.

## Open Questions

- Точное имя form-поля Nexara для granularities при multipart через httpx (массив) — уточнить при apply по их OpenAPI; при расхождении править только клиент Nexara.
