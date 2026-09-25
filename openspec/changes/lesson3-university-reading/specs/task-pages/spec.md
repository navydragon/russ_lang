# Spec Delta

## Purpose

Безопасная HTTP-раздача статических файлов заданий (HTML/JS/CSS) из каталога `tasks/`, включая вложенные каталоги уроков.

## ADDED Requirements

### Requirement: Serve nested task static files
The system SHALL serve files with allowed suffixes (`.html`, `.js`, `.css`, `.map`) from `tasks/` at URL path `/tasks/<relative-path>`, including one or more subdirectory segments (for example `/tasks/lesson3/university_reading.html`).

#### Scenario: Nested HTML is available
- **WHEN** a client requests `GET /tasks/lesson3/university_reading.html` and the file exists under `tasks/lesson3/`
- **THEN** the system returns the file contents with a successful HTTP status

#### Scenario: Flat task file still works
- **WHEN** a client requests `GET /tasks/class_speaking.html` and the file exists under `tasks/`
- **THEN** the system returns the file as before

### Requirement: Reject unsafe task paths
The system MUST reject requests whose resolved path escapes the `tasks/` directory or uses a disallowed suffix, without serving the file.

#### Scenario: Path traversal is blocked
- **WHEN** a client requests a path that would resolve outside `tasks/` (for example containing `..` segments meant to escape)
- **THEN** the system responds with HTTP 404 and does not serve a file outside `tasks/`

#### Scenario: Disallowed extension is blocked
- **WHEN** a client requests a path under `tasks/` whose suffix is not in the allowed set
- **THEN** the system responds with HTTP 404
