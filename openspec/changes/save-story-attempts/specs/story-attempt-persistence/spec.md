# Spec Delta

## Purpose

Описывает сохранение результата AI-проверки рассказа как попытки задания: идентификация студента по коду, запись оценки и подробностей после успешной проверки.

## ADDED Requirements

### Requirement: Persist story check as task attempt
После успешной HTTP-проверки рассказа система SHALL создать попытку задания (`TaskAttempt`), если переданы валидные код студента и код задания.

#### Scenario: Save after successful check
- **WHEN** клиент отправляет текст, `task_id`, непустой `student_code` и заполненный `task_code`, и LLM-проверка завершается успешно
- **THEN** система сохраняет попытку с `is_completed` равным `ok` результата проверки, баллом равным `score` (0–100) и подробным результатом в поле results

#### Scenario: Completion record when check ok
- **WHEN** проверка сохранена и поле `ok` результата равно true, и у студента ещё нет завершения этого задания
- **THEN** система создаёт запись о завершении задания студента

### Requirement: Soft-fail persistence
Система MUST вернуть результат AI-проверки даже если сохранение попытки невозможно; ответ SHALL включать признак, сохранена ли попытка.

#### Scenario: Missing student code
- **WHEN** LLM-проверка успешна, но `student_code` отсутствует или пуст
- **THEN** система возвращает результат проверки с `saved` = false и не создаёт попытку

#### Scenario: Placeholder or missing task code
- **WHEN** LLM-проверка успешна, но `task_code` отсутствует, пуст или является незаполненным плейсхолдером
- **THEN** система возвращает результат проверки с `saved` = false и не создаёт попытку

#### Scenario: Unknown student or task
- **WHEN** LLM-проверка успешна, но студент или задание по коду не найдены
- **THEN** система возвращает результат проверки с `saved` = false без ошибки 5xx из-за сохранения

### Requirement: Client sends identity and task code
Клиент урока SHALL передавать код студента из cookie `student_code` и захардкоженный `task_code` вместе с `task_id` и текстом на endpoint проверки рассказа.

#### Scenario: Payload includes student and task codes
- **WHEN** ученик нажимает «Отправить» и cookie `student_code` доступен
- **THEN** запрос к API проверки включает `student_code`, `task_code`, `task_id` и `text`

#### Scenario: Warn when not saved
- **WHEN** API возвращает успешную проверку с `saved` = false
- **THEN** UI показывает результат проверки и краткое предупреждение, что попытка не сохранена
