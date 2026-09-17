# Spec Delta

## Purpose

Проверка устной речи в speaking-уроках: серверная транскрибация через Nexara, сопоставление с эталонным словом и сохранение попытки только после трёх успешных ответов.

## ADDED Requirements

### Requirement: Transcribe speaking audio via Nexara
Система SHALL принимать аудиозапись и эталонное слово на backend endpoint проверки говорения и MUST транскрибировать аудио через Nexara `audio/transcriptions` с `response_format` = `verbose_json`.

#### Scenario: Successful transcription and match
- **WHEN** клиент отправляет валидный audio file и эталонное слово, и транскрипт содержит это слово (нормализованное сравнение)
- **THEN** система возвращает распознанный текст и `ok` = true

#### Scenario: Transcription without match
- **WHEN** транскрибация успешна, но эталонное слово не найдено в распознанном тексте
- **THEN** система возвращает распознанный текст и `ok` = false без ошибки 5xx

#### Scenario: Missing audio or reference
- **WHEN** в запросе нет файла аудио или эталонного слова
- **THEN** система отвечает ошибкой 400

#### Scenario: Nexara failure
- **WHEN** сервис транскрибации недоступен или возвращает ошибку
- **THEN** система отвечает ошибкой уровня 502/500 с сообщением о сбое транскрибации и не сохраняет попытку

### Requirement: Return check result to frontend
Система SHALL возвращать клиенту как минимум распознанный текст и признак зачёта шага, чтобы UI мог обновить прогресс 0/3…3/3.

#### Scenario: Frontend advances on ok
- **WHEN** API вернул `ok` = true для текущего объекта
- **THEN** клиент засчитывает шаг и переходит к следующему номеру (или завершает урок на 3/3)

### Requirement: Persist attempt only after three successful words
Система SHALL создавать `TaskAttempt` только когда ученик успешно назвал три слова в рамках одного прохождения урока.

#### Scenario: Save on lesson complete
- **WHEN** третий успешный шаг завершён и переданы валидные `student_code` и `task_code`
- **THEN** система сохраняет попытку с `is_completed` = true и подробным результатом (список шагов / транскрипты)

#### Scenario: No save before three successes
- **WHEN** выполнен только один или два успешных шага
- **THEN** система не создаёт `TaskAttempt` за это прохождение

#### Scenario: Soft-fail persistence
- **WHEN** урок завершён (3/3), но отсутствует student/task code или сохранение не удалось
- **THEN** UI всё равно показывает завершение урока, а ответ/клиент отражает, что попытка не сохранена, без падения проверки
