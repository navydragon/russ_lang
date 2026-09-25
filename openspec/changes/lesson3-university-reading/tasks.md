# Tasks

## 1. Nested task pages

- [x] 1.1 Обновить `config/task_pages.py`: разрешить relative path внутри `tasks/` (вложенные каталоги), guard от traversal, те же суффиксы. Verify: `GET /tasks/lesson3/...` и `GET /tasks/class_speaking.html` работают; path с `..` → 404.
- [x] 1.2 Обновить URL-pattern в `task_pages` под multi-segment path. Verify: regex/route принимает `lesson3/university_reading.html`.

## 2. Nexara word timestamps

- [x] 2.1 Расширить `api/speaking_nexara.py` (`transcribe_audio`): опция запроса `timestamp_granularities[]=word`; speaking path без изменений по умолчанию. Verify: при включённой опции в ответе есть `words` (или явная обработка отсутствия); speaking check не ломается.
- [x] 2.2 Добавить хелперы нормализации/токенов и извлечения `words[{word,start,end}]` из payload. Verify: unit-логика на фикстуре verbose_json (или ручной assert в модуле) извлекает список слов.

## 3. Reading API

- [x] 3.1 Добавить модуль эталона «Наш университет» (полный текст + границы предложений после `.`) и scoring: coverage ≥ 85% токенов, duration ≤ 180, паузы ≥ 0.30s, без stress/intonation. Verify: чистая функция на синтетических words проходит/фейлит сценарии из spec.
- [x] 3.2 Добавить `POST /api/reading/check` и `POST /api/reading/complete` в `api/views.py` + urls; complete → `save_quiz_result` по аналогии со speaking. Verify: маршруты зарегистрированы; check без файла → 400; complete без student_code → `saved: false`.

## 4. Lesson 3 UI

- [x] 4.1 Создать `tasks/lesson3/university_reading.html`: оболочка speaking/story, эталонный текст, запись, клиентский лимит 3 мин, вызов `/api/reading/check` и complete при `ok`, показ coverage/duration/пауз; `TASK_CODE` placeholder; `../api-config.js`. Verify: страница открывается по `/tasks/lesson3/university_reading.html`, в коде нет полей stress/intonation scoring.

## 5. Smoke

- [x] 5.1 Ручной smoke: открыть страницу, записать короткий фрагмент (или мок), убедиться что UI показывает результат API без 500 на nested path. Verify: нет 404 на nested HTML и нет 500 на reading/check при валидном multipart (или понятная ошибка Nexara без ключа).
