# Graph Report - russ_lang  (2026-11-12)

## Corpus Check
- 276 files · ~2,366,251 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 11, .css 2, .mdc 1)

## Summary
- 2145 nodes · 4076 edges · 172 communities (133 shown, 39 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 235 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e4eb1b0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- find_child
- AITestLauncherTests
- EmailForwarder
- course_sync.py
- dictation_views.py
- family_questions/questions.js
- Decimal
- register
- .agents/skills/openspec-explore/SKILL.md
- _io.py
- RemoveStudentFromGroupView
- User Management Template
- .cursor/skills/openspec-explore/SKILL.md
- Quiz Report Question Header Partial
- .form_valid
- ADDED Requirements
- Requirement: Общее подтверждение карточки
- .ready
- base.html Layout
- Quiz Question Status Header
- GroupAdmin
- story_llm.py
- json
- Proposal
- dictation.js
- classroom_questions.js
- UserCreateForm
- Урок 4
- RosterTests
- What You Must Do When Invoked
- Group
- deploy.sh
- EnrollmentServiceTests
- Student Lesson Results Template
- .get_context_data
- ADDED Requirements
- university_questions.py
- opsx-explore.md
- forwarder/apps.py
- generate_yandex_dictation_audio.py
- ADDED Requirements
- test_api_config.cjs
- faculty_questions/questions.js
- ADDED Requirements
- api/views.py
- Requirement: Persist attempt only after three successful words
- UserDeleteView
- ADDED Requirements
- Задания
- graphify reference: extra exports and benchmark
- import_tasks.py
- Proposal
- ADDED Requirements
- django-cors-headers
- openpyxl
- pydantic-ai
- update_prod.sh
- graphify reference: query, path, explain
- Задания для проверки ИИ
- users/views.py
- django_test
- CourseSyncTests
- Decisions
- Decisions
- questions.js
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- faculty_reading/reading.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md
- save_quiz_result
- CourseBindingTests
- Proposal
- Proposal
- .parse_user_id
- Tasks
- Tasks
- ProfilePasswordChangeView
- import_students.py
- Группы и студенты основного портала
- Проверка ударений в диктантах
- Результаты реализации
- Проверка реализации
- AI_4_1 — чтение «Мой университет»
- GroupForm
- excursion_questions/questions.js
- TaskAttempt
- Proposal
- pathlib
- ExcursionEndpointTests
- Материалы для новых заданий урока 7
- Урок 3
- Создание курса русского языка
- Requirement: Сервер измеряет длительность записи
- check_retelling_audio
- Design
- Tasks
- university_reading_part2/SOURCE.md
- LoginRequiredMixin
- Новые реализованные задания урока 5
- Урок 7 — комментарии к заданиям ИИ
- highlight.js
- reading.js
- email_forwarder.py
- Тексты, скопированные со слайдов
- AuthorReviewTests
- ADDED Requirements
- UserCreateView
- university_question_views.py
- reading_check.py
- SpeakingEndpointTests
- ADDED Requirements
- Proposal
- Proposal
- Requirement: Синхронизация выбранного курса
- Design
- Design
- Tasks
- Tasks
- ADDED Requirements
- Tasks
- Proposal
- Proposal
- Design
- test_roster.py
- Proposal
- Design
- fairytale_reading/reading.js
- django_db
- UserManagementView
- gagarin_reading/reading.js
- vdnh_reading/reading.js
- Tasks
- Design
- speaking_nexara.py
- Tasks
- lesson5/reading.js
- students/views.py
- Tasks
- juan_carlos_questions/questions.js
- QuestionSessionTests
- LibraryQuestionSessionTests

## God Nodes (most connected - your core abstractions)
1. `TaskAttempt` - 53 edges
2. `Student` - 44 edges
3. `Group` - 42 edges
4. `find_child()` - 38 edges
5. `find_children()` - 34 edges
6. `parse_question_base()` - 34 edges
7. `register_question_parser()` - 30 edges
8. `Course` - 29 edges
9. `Task` - 29 edges
10. `check_reading_audio()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `2. Nexara word timestamps` --references--> `transcribe_audio()`  [INFERRED]
  openspec/changes/lesson3-university-reading/tasks.md → api/speaking_nexara.py
- `What Changes` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/lesson3-university-reading/proposal.md → courses/models.py
- `New Capabilities` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/save-story-attempts/proposal.md → courses/models.py
- `Why` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/save-story-attempts/proposal.md → courses/models.py
- `Why` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/speaking-nexara-check/proposal.md → courses/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email Provider Configuration Set** — readme_gmail_provider, readme_yandex_provider, readme_mailru_provider, readme_outlook_provider, readme_env_configuration [EXTRACTED 1.00]
- **Quiz Report Page Assembly** — students_templates_quiz_report_report, students_templates_quiz_report__summary, students_templates_quiz_report__groups, students_templates_quiz_report_report_render_question [EXTRACTED 1.00]
- **Quiz Report Question Type Renderers** — students_templates_quiz_report_questions_multipleresponsequestion, students_templates_quiz_report_questions_numericquestion, students_templates_quiz_report_questions_sequencequestion, students_templates_quiz_report_questions_truefalsequestion, students_templates_quiz_report_questions_typeinquestion, students_templates_quiz_report_questions_unknown, students_templates_quiz_report_questions_wordbankquestion, students_templates_quiz_report__question_header [EXTRACTED 1.00]
- **Quiz Report Question Type Templates** — students_templates_quiz_report_questions_dndquestion_dnd, students_templates_quiz_report_questions_essayquestion_essay, students_templates_quiz_report_questions_fillintheblankquestion_fill_blank, students_templates_quiz_report_questions_hotspotquestion_hotspot, students_templates_quiz_report_questions_likertscalequestion_likert, students_templates_quiz_report_questions_matchingquestion_matching, students_templates_quiz_report_questions_multiplechoicequestion_mcq, students_templates_quiz_report_questions_multiplechoicetextquestion_mct [EXTRACTED 1.00]
- **Password Reset Flow** — users_templates_users_password_reset_subject, users_templates_users_password_reset_email, users_templates_users_password_reset_done, users_templates_users_password_reset_confirm, users_templates_users_password_reset_complete [INFERRED 0.85]
- **Quiz Report Shared Partials** — students_templates_quiz_report__question_header_question_status, students_templates_quiz_report__text_content_text_blocks, students_templates_quiz_report__question_body_dynamic_include, students_templates_quiz_report__summary_report_summary, students_templates_quiz_report__groups_group_results [INFERRED 0.85]
- **Student Group Management UI** — students_templates_students_group_management, students_templates_students_group_form, students_templates_students_group_students, students_templates_students_group_confirm_delete, students_templates_students_my_groups, students_templates_students_group_results [INFERRED 0.85]
- **User Management CRUD UI** — users_templates_users_user_management, users_templates_users_user_form, users_templates_users_user_confirm_delete, users_templates_users_user_password_change [INFERRED 0.85]

## Communities (172 total, 39 thin omitted)

### Community 0 - "find_child"
Cohesion: 0.06
Nodes (78): courses_quiz_report, detect_format(), _parse_groups(), _parse_question(), parse_quiz_report(), _parse_settings(), _parse_summary(), parse_summary_from_xml() (+70 more)

### Community 1 - "AITestLauncherTests"
Cohesion: 0.13
Nodes (6): AITestLauncherTests, AssignmentReviewConfirmationTests, override_settings, TestCase, _TaskAssetParser, HTMLParser

### Community 2 - "EmailForwarder"
Cohesion: 0.12
Nodes (15): EmailForwarder, Парсит HTML письма и извлекает структурированные данные Args: html_body: HTML…, Выводит User ID в консоль Args: user_id: User ID для вывода subject: Тема…, Находит студента в базе данных по коду с загрузкой группы и кураторов Args:…, Находит кураторов группы студента Args: student: Объект Student Returns: Список…, Получает email кураторов группы студента с включённым флагом send_emails Args:…, Подключение к IMAP серверу, Подключение к SMTP серверу (+7 more)

### Community 3 - "course_sync.py"
Cohesion: 0.29
Nodes (8): apply_plan(), build_plan(), DesiredTask, Добавление курса и заданий без очистки таблиц и потери результатов., read_regular_tasks(), SyncPlan, Command, BaseCommand

### Community 4 - "dictation_views.py"
Cohesion: 0.06
Nodes (31): choose_words(), grade_answer(), public_state(), Диктант AI_3_7: фиксированный эталон, случайный набор и прозрачные баллы., run_score(), answer(), _body(), _find_session() (+23 more)

### Community 5 - "family_questions/questions.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 6 - "Decimal"
Cohesion: 0.29
Nodes (7): extract_score_percent(), extract_score_value(), Any, Извлекает процент из строки score. Примеры: - "10 / 10 (100%)" -> 100.00 - "5 /…, Извлекает числовое значение баллов из строки score. Примеры: - "10 / 10 (100%)"…, _to_decimal(), Decimal

### Community 7 - "register"
Cohesion: 0.11
Nodes (15): CourseAdmin, LessonAdmin, register, Возвращает количество уроков в курсе., Админ-интерфейс для модели Lesson., Возвращает количество заданий в уроке., Админ-интерфейс для модели Task., Возвращает количество попыток выполнения задания. (+7 more)

### Community 8 - ".agents/skills/openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 9 - "_io.py"
Cohesion: 0.08
Nodes (38): fractions, functools, importlib_resources, _get_arch(), _get_os_string(), get_platform(), imageio_ffmpeg, FFMPEG wrapper for Python., count_frames_and_secs() (+30 more)

### Community 10 - "RemoveStudentFromGroupView"
Cohesion: 0.06
Nodes (25): GroupCreateView, GroupDeleteView, GroupManagementView, GroupResultsView, GroupStudentsView, GroupUpdateView, MyGroupsView, CreateView (+17 more)

### Community 11 - "User Management Template"
Cohesion: 0.13
Nodes (17): Student Remove Confirm Template, Soft Remove From Group, Admin Panel Template, Admin Panel Stub, Password Reset Complete Template, Password Reset Confirm Template, Password Reset Done Template, Password Reset Email Template (+9 more)

### Community 12 - ".cursor/skills/openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 13 - "Quiz Report Question Header Partial"
Cohesion: 0.20
Nodes (15): Quiz Report Groups Partial, Quiz Report Question Header Partial, Quiz Report Summary Partial, Quiz Report Text Content Partial, Multiple Response Question Template, Numeric Question Template, Numeric Acceptable Answer Rules, Sequence Question Template (+7 more)

### Community 14 - ".form_valid"
Cohesion: 0.18
Nodes (6): PasswordResetConfirmView, PasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetView, Представление для установки нового пароля., Представление для запроса сброса пароля.

### Community 15 - "ADDED Requirements"
Cohesion: 0.14
Nodes (13): ADDED Requirements, Purpose, Requirement: Client sends identity and task code, Requirement: Persist story check as task attempt, Requirement: Soft-fail persistence, Scenario: Completion record when check ok, Scenario: Missing student code, Scenario: Payload includes student and task codes (+5 more)

### Community 16 - "Requirement: Общее подтверждение карточки"
Cohesion: 0.17
Nodes (11): ADDED Requirements, Purpose, Requirement: Дата правок на карточке, Requirement: Общее подтверждение карточки, Scenario: Дата правки отсутствует, Scenario: Изменённое задание, Scenario: Неизвестный код или режим без DEBUG, Scenario: Ошибка сохранения (+3 more)

### Community 17 - ".ready"
Cohesion: 0.18
Nodes (4): ForwarderConfig, start_forwarder(), AppConfig, Запускает email_forwarder в отдельном потоке при старте Django. Запускается…

### Community 18 - "base.html Layout"
Cohesion: 0.29
Nodes (11): base.html Layout, Group Confirm Delete Template, Non-Empty Group Delete Guard, Group Form Template, Group Form Fields (name, code, curators), Group Management Template, Group Results Template, Group Students Template (+3 more)

### Community 19 - "Quiz Question Status Header"
Cohesion: 0.29
Nodes (11): Quiz Question Body Dynamic Include, Quiz Question Status Header, Quiz Text Content Blocks, dndQuestion, essayQuestion, fillInTheBlankQuestion, hotspotQuestion, likertScaleQuestion (+3 more)

### Community 20 - "GroupAdmin"
Cohesion: 0.20
Nodes (7): GroupAdmin, register, Админ-интерфейс для модели Group., Возвращает список кураторов через запятую., Возвращает количество студентов в группе., Админ-интерфейс для модели Student., StudentAdmin

### Community 21 - "story_llm.py"
Cohesion: 0.16
Nodes (25): Agent, check_sentence_rubric(), check_vocab_rubric(), _count_sentences(), _get_about_me_agent(), _get_agent(), _is_optional_vocab_nag(), _merge_recommendations() (+17 more)

### Community 22 - "json"
Cohesion: 0.29
Nodes (6): Shared source and exact targets for the three Moscow excursion tasks., score_selection(), words_and_targets(), ExcursionSourceTests, SimpleTestCase, json

### Community 23 - "Proposal"
Cohesion: 0.29
Nodes (6): Capabilities, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 24 - "dictation.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 25 - "classroom_questions.js"
Cohesion: 0.26
Nodes (10): CARDS, chunks, currentState(), el(), pairText(), render(), renderGrade(), sendCheck() (+2 more)

### Community 26 - "UserCreateForm"
Cohesion: 0.13
Nodes (10): django_contrib_auth_forms, django_contrib_messages, UserCreationForm, Создание пользователя с вводом и подтверждением пароля., Форма для создания и редактирования пользователя администратором., UserCreateForm, UserForm, override_settings (+2 more)

### Community 27 - "Урок 4"
Cohesion: 0.11
Nodes (18): 18. 3.1 Чтение текста «Мой университет» — часть 1, 19. 3.4.1 Письменный пересказ «Мой университет»: друзья и спортзал, 20. Задание № 22. Ответы по тексту «Мой университет», 21. 3.8.1 Письменный пересказ текста «Мой университет», 22. 3.15.1 Чтение текста «Наш район и наша улица», 23. 3.19.1 Сочинение «Моя семья», 24. 4.1 Чтение диалога, 25. 4.2.1 Рассказ о себе по плану (+10 more)

### Community 28 - "RosterTests"
Cohesion: 0.07
Nodes (23): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Open Questions, Risks / Trade-offs, Context (+15 more)

### Community 29 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 30 - "Group"
Cohesion: 0.09
Nodes (36): contextlib, validate_websoft_id(), django_core, django_core_exceptions, django_views_decorators_debug, Exception, HTTPRedirectHandler, require_http_methods (+28 more)

### Community 31 - "deploy.sh"
Cohesion: 0.60
Nodes (5): die(), log(), read_env_value(), deploy.sh script, unit_exists()

### Community 32 - "EnrollmentServiceTests"
Cohesion: 0.15
Nodes (5): EnrollmentResponseTests, EnrollmentServiceTests, override_settings, patch, TestCase

### Community 33 - "Student Lesson Results Template"
Cohesion: 0.50
Nodes (4): Student Lesson Results Template, Attempt Results Modal, render_attempt_results Tag, Task Name Search Filter

### Community 34 - ".get_context_data"
Cohesion: 0.20
Nodes (9): AdminPasswordChangeForm, Форма для смены пароля пользователя администратором. Использует встроенную…, UserPasswordChangeForm, AdminPanelView, TemplateView, UserPassesTestMixin, Представление для смены пароля пользователя администратором., Страница-заглушка для администрирования. Доступна только для пользователей с… (+1 more)

### Community 35 - "ADDED Requirements"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Purpose, Requirement: Lesson 3 reading task UI, Requirement: Persist completed reading attempt, Requirement: Reading check does not score stress or enumeration intonation, Requirement: Reading check evaluates coverage, duration, and period pauses, Scenario: Attempt saved on complete, Scenario: Incomplete coverage fails the check (+7 more)

### Community 36 - "university_questions.py"
Cohesion: 0.22
Nodes (8): _get_agent(), AI_4_3: independent semantic and writing checks for one written answer., httpx, pydantic, pydantic_ai, pydantic_ai_models_openai, pydantic_ai_providers_openai, secrets

### Community 37 - "opsx-explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 38 - "forwarder/apps.py"
Cohesion: 0.13
Nodes (10): ApiConfig, AppConfig, CoursesConfig, AppConfig, django_apps, AppConfig, StudentsConfig, threading (+2 more)

### Community 39 - "generate_yandex_dictation_audio.py"
Cohesion: 0.06
Nodes (57): argparse, array, base64, ASGI config for russ_lang project. It exposes the ASGI callable as a module-…, Явный профиль БД из .env для синхронизации курса; локальный сервер не…, Isolated URL configuration avoids unrelated pre-existing merge conflicts., Django settings for russ_lang project., WSGI config for russ_lang project. It exposes the WSGI callable as a module-… (+49 more)

### Community 40 - "ADDED Requirements"
Cohesion: 0.09
Nodes (21): ADDED Requirements, Purpose, Requirement: Доназначение текущим студентам, Requirement: Защищённое назначение, Requirement: Назначение при сохранении студента, Requirement: Несколько курсов группы, Requirement: Связь курса с WebSoft, Requirement: Сохранность назначений и результатов (+13 more)

### Community 41 - "test_api_config.cjs"
Cohesion: 0.20
Nodes (9): ref_node_assert_strict, ref_node_fs, ref_node_path, ref_node_vm, assert, fs, path, script (+1 more)

### Community 42 - "faculty_questions/questions.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 43 - "ADDED Requirements"
Cohesion: 0.09
Nodes (21): ADDED Requirements, Purpose, Requirement: Защита удаления группы, Requirement: Защищённый серверный обмен, Requirement: Изолированное управление членством, Requirement: Обновление данных без смены пароля, Requirement: Общие уникальные ключи, Requirement: Повторяемые операции (+13 more)

### Community 44 - "api/views.py"
Cohesion: 0.24
Nodes (19): excursion_highlight_check(), _is_usable_task_code(), neighborhood_verbs_check(), _persist_reading_attempt(), _persist_speaking_attempt(), _persist_story_attempt(), picture_question_check(), csrf_exempt (+11 more)

### Community 45 - "Requirement: Persist attempt only after three successful words"
Cohesion: 0.13
Nodes (14): ADDED Requirements, Purpose, Requirement: Persist attempt only after three successful words, Requirement: Return check result to frontend, Requirement: Transcribe speaking audio via Nexara, Scenario: Frontend advances on ok, Scenario: Missing audio or reference, Scenario: Nexara failure (+6 more)

### Community 46 - "UserDeleteView"
Cohesion: 0.33
Nodes (3): DeleteView, Представление для удаления пользователя., UserDeleteView

### Community 47 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Purpose, Requirement: Reject unsafe task paths, Requirement: Serve nested task static files, Scenario: Disallowed extension is blocked, Scenario: Flat task file still works, Scenario: Nested HTML is available, Scenario: Path traversal is blocked (+1 more)

### Community 48 - "Задания"
Cohesion: 0.12
Nodes (16): Вопросы по тексту «Мой университет», Задания, Измерение длительности аудио, Локальная проверка, Подтверждение правок, Пробная озвучка Yandex SpeechKit, Разделение чтения «Мой университет», Текущая озвучка всех диктантов — Yandex SpeechKit (+8 more)

### Community 49 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 50 - "import_tasks.py"
Cohesion: 0.29
Nodes (4): collections, Command, BaseCommand, django_db_models

### Community 57 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 59 - "ADDED Requirements"
Cohesion: 0.10
Nodes (20): ADDED Requirements, Purpose, Requirement: Доступ к управлению, Requirement: Импорт в выбранную группу, Requirement: Результат частичного импорта, Requirement: Создание и редактирование студента, Requirement: Удаление членства и пустой группы, Requirement: Управление группами (+12 more)

### Community 70 - "update_prod.sh"
Cohesion: 0.46
Nodes (7): log_error(), log_info(), log_warn(), read_env_value(), update_prod.sh script, unit_exists(), usage()

### Community 71 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 72 - "Задания для проверки ИИ"
Cohesion: 0.17
Nodes (12): 1. Рассказ «Семья», 2. Рассказ «Комната», 3. Говорение по картинке «Город», 4. Говорение по картинке «Аудитория», 5. Говорение по картинке «Квартира», 6. 2.2 Чтение текста «Мой фотоальбом», 7. 2.4 Рассказ о своей семье по фотографии, Задания для проверки ИИ (+4 more)

### Community 73 - "users/views.py"
Cohesion: 0.17
Nodes (9): django_contrib_auth_mixins, django_contrib_auth_views, django_views_generic, PasswordResetCompleteView, PasswordResetDoneView, CustomPasswordResetCompleteView, CustomPasswordResetDoneView, Представление для подтверждения отправки письма со ссылкой для сброса пароля. (+1 more)

### Community 74 - "django_test"
Cohesion: 0.16
Nodes (11): decision(), override_settings, SimpleTestCase, QuestionGradingTests, AnswerGrade, choose_words(), grade_answer(), BaseModel (+3 more)

### Community 76 - "Decisions"
Cohesion: 0.15
Nodes (12): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs, Идемпотентность и конкурентная запись, Импорт и формы (+4 more)

### Community 77 - "Decisions"
Cohesion: 0.17
Nodes (11): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs, Использование штатного назначения, Контракт назначения (+3 more)

### Community 78 - "questions.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 79 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 80 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 81 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 82 - "faculty_reading/reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 96 - "save_quiz_result"
Cohesion: 0.10
Nodes (25): check_story(), story_check(), Сохраняет результат выполнения задания в базу данных. Args: parsed_data:…, save_quiz_result(), Context, Decisions, Design, Goals / Non-Goals (+17 more)

### Community 98 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 99 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 100 - ".parse_user_id"
Cohesion: 0.33
Nodes (3): __init__(), Инициализация пересылки писем Args: imap_server: Адрес IMAP сервера (например,…, Парсит User ID из текста письма Args: text_body: Текстовая версия письма…

### Community 101 - "Tasks"
Cohesion: 0.29
Nodes (6): 1. Привязка курсов и модели, 2. API назначения в отдельном репозитории WebSoft, 3. Общий сервис назначения Django, 4. Интерфейс группы и импорт, 5. Совместная приёмка и развёртывание, Tasks

### Community 102 - "Tasks"
Cohesion: 0.29
Nodes (6): 1. Контракт и операции WebSoft API, 2. Локальные модели и адаптер russ_lang, 3. Интерфейс управления, 4. Шаблон и импорт, 5. Совместная проверка и готовность к развёртыванию, Tasks

### Community 103 - "ProfilePasswordChangeView"
Cohesion: 0.40
Nodes (3): PasswordChangeView, ProfilePasswordChangeView, Представление для изменения пароля пользователя.

### Community 104 - "import_students.py"
Cohesion: 0.26
Nodes (7): django_utils_crypto, Command, group_code_from_name(), normalize(), parse_curator_name(), BaseCommand, username_from_email()

### Community 105 - "Группы и студенты основного портала"
Cohesion: 0.29
Nodes (6): Группы и студенты основного портала, Импорт, Курсы WebSoft, Подключение, Проверка, Развёртывание и откат

### Community 106 - "Проверка ударений в диктантах"
Cohesion: 0.33
Nodes (5): dictation_1, dictation_2, Исправление разметки Microsoft IPA, Проверка ударений в диктантах, Текущая озвучка SpeechKit

### Community 107 - "Результаты реализации"
Cohesion: 0.33
Nodes (5): Готовность и ограничения, Локальный WebSoft, Проверки Django, Результаты реализации, Сквозная и браузерная проверки

### Community 108 - "Проверка реализации"
Cohesion: 0.33
Nodes (5): Django, Локальный WebSoft, Ограничения готовности, Проверка реализации, Сквозная проверка

### Community 109 - "AI_4_1 — чтение «Мой университет»"
Cohesion: 0.29
Nodes (6): AI_4_1 — чтение «Мой университет», Актуальное разделение и синтез, Текст, Формат задания, Часть 1, Часть 2

### Community 110 - "GroupForm"
Cohesion: 0.20
Nodes (5): main(), group_form(), GroupForm, Meta, Форма для создания и редактирования группы.

### Community 111 - "excursion_questions/questions.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 112 - "TaskAttempt"
Cohesion: 0.10
Nodes (27): courses_course_sync, Command, BaseCommand, Command, atomic, BaseCommand, Command, atomic (+19 more)

### Community 113 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 114 - "pathlib"
Cohesion: 0.08
Nodes (32): Раздача HTML-уроков из каталога tasks/ по HTTP (не file://)., Отдаёт безопасные файлы из tasks/ (html/js/css), включая вложенные каталоги., serve_task_file(), URL configuration for russ_lang project., _assignment_details(), author_assignments(), author_set_confirmation(), _plain_details() (+24 more)

### Community 115 - "ExcursionEndpointTests"
Cohesion: 0.25
Nodes (3): ExcursionEndpointTests, override_settings, TestCase

### Community 116 - "Материалы для новых заданий урока 7"
Cohesion: 0.29
Nodes (6): 14.1 Чтение «ВДНХ», 15.1–15.3 Сказка «Богач и бедняк», 27.2–27.3 «Первый космический полёт», 35.1 Изложение «Вечер на факультете», Материалы для новых заданий урока 7, Общие недостающие решения

### Community 117 - "Урок 3"
Cohesion: 0.18
Nodes (11): 10. 2.4.1 Рассказ «Мой университет», 11. 2.16 Чтение текста «Москва — столица», 12. 2.18.1 Пересказ текста «Москва — столица» по опорным словам, 13. 3.2.1 Диктант № 1, 14. 3.2.1 Диктант № 2, 15. Диктант № 3 со списком слов, 16. 3.4 Диктант с текстом о Новгороде, 17. 3.4.1 Пересказ текста «Новгород» по плану (+3 more)

### Community 118 - "Создание курса русского языка"
Cohesion: 0.18
Nodes (7): Выполненный запуск, Исключённый дубль, Коды ИИ-заданий, Подключение к PostgreSQL, Подключение через SSH, Создание курса русского языка, Слова диктанта AI_3_7

### Community 119 - "Requirement: Сервер измеряет длительность записи"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Purpose, Requirement: Сервер измеряет длительность записи, Scenario: Длительность недоступна, Scenario: Запись укладывается в лимит, Scenario: Лимит не установлен, Scenario: Превышен лимит задания, Scenario: Противоречие ответа распознавания (+1 more)

### Community 120 - "check_retelling_audio"
Cohesion: 0.13
Nodes (8): check_retelling_audio(), _build_user_prompt(), NovgorodRetellingTests, SimpleTestCase, retelling_result(), RetellingTests, VDNHRetellingTests, django_core_files_uploadedfile

### Community 121 - "Design"
Cohesion: 0.29
Nodes (6): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 122 - "Tasks"
Cohesion: 0.40
Nodes (4): 1. Данные и сохранение, 2. Страница, 3. Проверка и документация, Tasks

### Community 124 - "LoginRequiredMixin"
Cohesion: 0.16
Nodes (11): Meta, ProfileEditForm, Форма для редактирования данных профиля пользователя., ProfileEditView, ProfileView, LoginRequiredMixin, UpdateView, Главная страница профиля пользователя с вкладками. (+3 more)

### Community 125 - "Новые реализованные задания урока 5"
Cohesion: 0.22
Nodes (9): 47. 6.1.1 Вопросы и ответы по картинкам «В классе», 48. 13.1.1 Ответы на вопросы по тексту «Хуан и Карлос», 49. 15.1.1 Ответы на вопросы по тексту «Наша семья», Новые реализованные задания урока 5, Чтение «В классе», Чтение «Наша семья», Чтение «Попугай», Чтение «Томас и Эдвард — студенты» (+1 more)

### Community 126 - "Урок 7 — комментарии к заданиям ИИ"
Cohesion: 0.15
Nodes (13): 35. 14.3 Пересказ текста по опорам, 36. Задание № 26. Подчеркнуть формы слов и выражения времени, 37. 29.1 Чтение текста «Экскурсия по Москве», 38. 29.1 Письменные ответы по тексту «Экскурсия по Москве», 39. Чтение «Вечер на факультете», 40. Вопросы по тексту «Вечер на факультете», 41. 14.1 Чтение «ВДНХ», 42. 15.3 Чтение «Богач и бедняк» (+5 more)

### Community 127 - "highlight.js"
Cohesion: 0.40
Nodes (5): addText(), paint(), selected, sourceEl, spans

### Community 128 - "reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 129 - "email_forwarder.py"
Cohesion: 0.05
Nodes (40): AbstractUser, BaseUserAdmin, django_contrib_auth_admin, django_contrib_auth_models, django_contrib_auth_validators, django_utils_timezone, email, email_header (+32 more)

### Community 131 - "Тексты, скопированные со слайдов"
Cohesion: 0.20
Nodes (10): 12.1 «Хуан и Карлос», 14.1 «Наша семья», 23.1 «Попугай», 24.4 «Томас и Эдвард — студенты», 5.1 «В классе», Вопросы со слайда 24.2 к тексту «Попугай», Материалы новых заданий урока 5, Примечания для подготовки карточек (+2 more)

### Community 134 - "AuthorReviewTests"
Cohesion: 0.33
Nodes (3): AuthorReviewTests, override_settings, TestCase

### Community 135 - "ADDED Requirements"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Purpose, Requirement: Видовые пары сказки, Requirement: Каталог и проверка, Requirement: Письменное изложение, Requirement: Три задания на чтение, Requirement: Устный пересказ сказки, Scenario: Автор открывает новое задание (+7 more)

### Community 136 - "UserCreateView"
Cohesion: 0.40
Nodes (3): CreateView, Представление для создания нового пользователя., UserCreateView

### Community 137 - "university_question_views.py"
Cohesion: 0.19
Nodes (16): answer(), _body(), _find_session(), _old_lesson7_run(), atomic, csrf_exempt, require_GET, require_POST (+8 more)

### Community 138 - "reading_check.py"
Cohesion: 0.06
Nodes (36): align_reference_to_words(), align_reference_with_gaps(), build_reading_correct_prompt(), check_reading_audio(), coverage_ratio(), extract_corrected_text(), period_boundary_token_indices(), Any (+28 more)

### Community 139 - "SpeakingEndpointTests"
Cohesion: 0.50
Nodes (3): patch, SimpleTestCase, SpeakingEndpointTests

### Community 140 - "ADDED Requirements"
Cohesion: 0.15
Nodes (12): ADDED Requirements, Purpose, Requirement: Вопросы по вечеру, Requirement: Вопросы по экскурсии, Requirement: Пересказ ВДНХ по опорам, Requirement: Продолжение начатых попыток, Scenario: Возобновление старой попытки, Scenario: Завершение ответов (+4 more)

### Community 141 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 142 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 143 - "Requirement: Синхронизация выбранного курса"
Cohesion: 0.25
Nodes (7): ADDED Requirements, Requirement: Синхронизация выбранного курса, Scenario: Конфликт кода, Scenario: Курс отсутствует, Scenario: Повторное применение, Scenario: Предварительный просмотр, Scenario: Совместимость

### Community 144 - "Design"
Cohesion: 0.33
Nodes (5): Context, Decisions, Design, Goals / Non-Goals, Risks / Trade-offs

### Community 146 - "Design"
Cohesion: 0.29
Nodes (6): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 147 - "Tasks"
Cohesion: 0.40
Nodes (4): 1. Серверное измерение, 2. Интерфейс и окружение, 3. Проверка и документация, Tasks

### Community 149 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Purpose, Requirement: Проверка чтения и сохранение результата, Requirement: Чтение текстов урока 5, Scenario: Запись превышает установленный лимит, Scenario: Запись чтения остальных текстов, Scenario: Запись чтения текста «В классе», Scenario: Студент отправил запись в пределах лимита (+1 more)

### Community 150 - "Tasks"
Cohesion: 0.29
Nodes (6): 1. Nested task pages, 2. Nexara word timestamps, 3. Reading API, 4. Lesson 3 UI, 5. Smoke, Tasks

### Community 153 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 154 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 155 - "Design"
Cohesion: 0.29
Nodes (6): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 156 - "test_roster.py"
Cohesion: 0.11
Nodes (21): django, django_contrib_auth, django_db_migrations_executor, django_test_utils, django_urls, openpyxl, openpyxl_utils_exceptions, Opt-in local integration check. Requires owned enrollment_fixture.html… (+13 more)

### Community 157 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 158 - "Design"
Cohesion: 0.29
Nodes (6): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 159 - "fairytale_reading/reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 160 - "django_db"
Cohesion: 0.07
Nodes (15): Migration, Migration, Migration, django_db, django_db_models_deletion, Migration, Migration, Migration (+7 more)

### Community 161 - "UserManagementView"
Cohesion: 0.40
Nodes (3): ListView, Главная страница управления пользователями со списком всех пользователей.…, UserManagementView

### Community 162 - "gagarin_reading/reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 163 - "vdnh_reading/reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 164 - "Tasks"
Cohesion: 0.50
Nodes (3): 1. Изменение заданий, 2. Проверка и описание, Tasks

### Community 165 - "Design"
Cohesion: 0.29
Nodes (6): Context, Decisions, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 166 - "speaking_nexara.py"
Cohesion: 0.20
Nodes (15): AudioDurationError, measure_audio_duration(), Measure uploaded audio duration by decoding it with the bundled FFmpeg., Устный пересказ: ASR и проверка содержания, без имитации оценки ударения., check_speaking_audio(), extract_recognized_text(), normalize_nexara_payload(), Any (+7 more)

### Community 167 - "Tasks"
Cohesion: 0.40
Nodes (4): 1. Источники и чтение, 2. Грамматика и пересказы, 3. Каталог и проверка, Tasks

### Community 168 - "lesson5/reading.js"
Cohesion: 0.40
Nodes (4): buttons(), chunks, el(), stop()

### Community 169 - "students/views.py"
Cohesion: 0.14
Nodes (11): django_contrib, django_contrib_auth_decorators, login_required, LoginView, LogoutView, CustomLoginView, CustomLogoutView, index() (+3 more)

### Community 172 - "Tasks"
Cohesion: 0.40
Nodes (4): 1. Тексты и аудиообразцы, 2. Страницы и проверка чтения, 3. Каталог и перечень, Tasks

### Community 174 - "juan_carlos_questions/questions.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 180 - "LibraryQuestionSessionTests"
Cohesion: 0.24
Nodes (5): LibraryQuestionBankTests, LibraryQuestionSessionTests, override_settings, SimpleTestCase, TestCase

## Ambiguous Edges - Review These
- `students:my_groups` → `Quiz Report Group Results`  [AMBIGUOUS]
  students/templates/quiz_report/_groups.html · relation: conceptually_related_to

## Knowledge Gaps
- **472 isolated node(s):** `Migration`, `Migration`, `Migration`, `PlannedAssignment`, `assert` (+467 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 954 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `students:my_groups` and `Quiz Report Group Results`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `TaskAttempt` connect `TaskAttempt` to `AITestLauncherTests`, `dictation_views.py`, `reading_check.py`, `RemoveStudentFromGroupView`, `ADDED Requirements`, `json`, `Proposal`, `test_roster.py`, `RosterTests`, `EnrollmentServiceTests`, `ADDED Requirements`, `students/views.py`, `Requirement: Persist attempt only after three successful words`, `QuestionSessionTests`, `LibraryQuestionSessionTests`, `Proposal`, `django_test`, `CourseSyncTests`, `save_quiz_result`, `import_students.py`, `GroupForm`, `pathlib`, `ExcursionEndpointTests`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Student` connect `TaskAttempt` to `EnrollmentServiceTests`, `email_forwarder.py`, `AITestLauncherTests`, `EmailForwarder`, `import_students.py`, `students/views.py`, `RemoveStudentFromGroupView`, `CourseSyncTests`, `RosterTests`, `GroupForm`, `pathlib`, `test_roster.py`, `Group`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Group` connect `Group` to `EnrollmentServiceTests`, `AITestLauncherTests`, `import_students.py`, `students/views.py`, `RemoveStudentFromGroupView`, `RosterTests`, `GroupForm`, `TaskAttempt`, `test_roster.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `TaskAttempt` (e.g. with `DictationAPITests` and `NovgorodDictationAPITests`) actually correct?**
  _`TaskAttempt` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Student` (e.g. with `Command` and `StudentTask`) actually correct?**
  _`Student` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Group` (e.g. with `Command` and `AITestLauncherTests`) actually correct?**
  _`Group` has 23 INFERRED edges - model-reasoned connections that need verification._