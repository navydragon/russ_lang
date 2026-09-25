# Spec Delta

## Purpose

Контроль чтения эталонного русского текста вслух: транскрипция, покрытие эталона, лимит времени и проверка пауз после точки; UI задания урока 3 «Наш университет».

## ADDED Requirements

### Requirement: Reading check evaluates coverage, duration, and period pauses
The system SHALL accept a multipart audio upload for reading check together with identification fields needed to score against the fixed reference text «Наш университет», and SHALL return JSON that includes at least: recognized transcript, duration (when available from ASR), coverage outcome, per-sentence pause outcomes after periods, and an overall `ok` boolean.

#### Scenario: Successful reading within time with pauses
- **WHEN** the learner submits audio that covers the reference text, duration is at most 180 seconds, and each inter-sentence gap after a period meets the configured minimum pause
- **THEN** the response has `ok` true and reports passing coverage, duration, and pause details

#### Scenario: Missing pause after a period fails the check
- **WHEN** the learner submits audio that otherwise covers the text within 180 seconds but at least one gap after a sentence-ending period is below the configured minimum pause
- **THEN** the response has `ok` false and identifies which period pause(s) failed

#### Scenario: Over-time reading fails the check
- **WHEN** ASR reports duration greater than 180 seconds
- **THEN** the response has `ok` false for the duration criterion

#### Scenario: Incomplete coverage fails the check
- **WHEN** the normalized recognized transcript does not adequately cover the normalized reference text according to the coverage rule
- **THEN** the response has `ok` false for coverage

### Requirement: Reading check does not score stress or enumeration intonation
The system MUST NOT require or return automatic scores for lexical stress or enumeration intonation as part of the reading check.

#### Scenario: Response omits stress and intonation scoring
- **WHEN** a reading check completes successfully or with failures on coverage/duration/pauses
- **THEN** the response does not include stress or enumeration-intonation score fields as pass/fail criteria

### Requirement: Persist completed reading attempt
After a successful reading check (`ok` true), the client MAY request persistence; the system SHALL save a `TaskAttempt` when `student_code` is present and `task_code` is usable (not a placeholder), using the same persistence pathway as other AI tasks.

#### Scenario: Attempt saved on complete
- **WHEN** the client posts a reading complete payload with valid `student_code` and usable `task_code` after `ok` true
- **THEN** the system returns `saved` true (or an explicit save error) and persists the attempt when save succeeds

#### Scenario: Soft-fail without student identity
- **WHEN** the complete request lacks `student_code` or still has a placeholder `task_code`
- **THEN** the system does not crash and returns `saved` false with a reason, without blocking the UI from showing the reading result

### Requirement: Lesson 3 reading task UI
The system SHALL provide a lesson-3 reading page under `tasks/lesson3/` that shows the reference text «Наш университет», allows microphone recording with a 3-minute time limit, calls the reading check API, and displays coverage, duration, and pause results in the project task shell style.

#### Scenario: Learner records and sees pause feedback
- **WHEN** the learner opens the lesson-3 reading page, records reading, and submits for check
- **THEN** the page shows recognized text (or equivalent summary), duration status, and per-period pause pass/fail feedback from the API
