# Graph Report - russ_lang  (2026-10-25)

## Corpus Check
- 160 files · ~1,116,275 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .mdc 1, .example 1)

## Summary
- 1215 nodes · 2272 edges · 104 communities (69 shown, 35 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 155 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9ae1ba23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- find_child
- parser.py
- EmailForwarder
- story_llm.py
- test_dictation.py
- Student
- api/views.py
- register
- email_forwarder.py
- django_conf
- GroupResultsView
- User Management Template
- UserForm
- Quiz Report Question Header Partial
- .form_valid
- ADDED Requirements
- reading_check.py
- import_students.py
- base.html Layout
- Quiz Question Status Header
- GroupAdmin
- dictation_views.py
- test_ai_test_launcher.py
- TaskAttempt
- dictation.js
- UserUpdateView
- GroupUpdateView
- Урок 4
- .ready
- What You Must Do When Invoked
- DictationAPITests
- deploy.sh
- PluralDictationAPITests
- Student Lesson Results Template
- LoginRequiredMixin
- ADDED Requirements
- students/views.py
- opsx-explore.md
- forwarder/apps.py
- generate_yandex_dictation_audio.py
- RemoveStudentFromGroupView
- test_api_config.cjs
- os
- .agents/skills/openspec-explore/SKILL.md
- Task
- Requirement: Persist attempt only after three successful words
- ProfileEditView
- ADDED Requirements
- Задания
- graphify reference: extra exports and benchmark
- users/views.py
- Proposal
- .cursor/skills/openspec-explore/SKILL.md
- django-cors-headers
- openpyxl
- pydantic-ai
- update_prod.sh
- graphify reference: query, path, explain
- course_sync.py
- GroupCreateView
- AITestLauncherTests
- CourseSyncTests
- GroupManagementView
- courses/migrations/0001_initial.py
- ProfilePasswordChangeView
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- Group
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md
- OpenSpec Awareness
- DictationPronunciationTests
- UserCreateView
- Command
- OpenSpec Awareness
- courses/apps.py
- .get_context_data
- Проверка ударений в диктантах

## God Nodes (most connected - your core abstractions)
1. `find_child()` - 38 edges
2. `TaskAttempt` - 34 edges
3. `find_children()` - 34 edges
4. `parse_question_base()` - 34 edges
5. `register_question_parser()` - 30 edges
6. `save_quiz_result()` - 28 edges
7. `Student` - 27 edges
8. `AITestLauncherTests` - 25 edges
9. `Task` - 23 edges
10. `Group` - 23 edges

## Surprising Connections (you probably didn't know these)
- `What Changes` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/lesson3-university-reading/proposal.md → courses/models.py
- `New Capabilities` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/save-story-attempts/proposal.md → courses/models.py
- `Why` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/save-story-attempts/proposal.md → courses/models.py
- `Scenario: No save before three successes` --references--> `TaskAttempt`  [INFERRED]
  openspec/changes/speaking-nexara-check/specs/speaking-check/spec.md → courses/models.py
- `Impact` --references--> `save_quiz_result()`  [INFERRED]
  openspec/changes/lesson3-university-reading/proposal.md → courses/services.py

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

## Communities (104 total, 35 thin omitted)

### Community 0 - "find_child"
Cohesion: 0.14
Nodes (47): parse_dnd(), _parse_objects(), _parse_placements(), Element, parse_essay(), Element, parse_fill_in_blank(), Element (+39 more)

### Community 1 - "parser.py"
Cohesion: 0.08
Nodes (31): courses_quiz_report, detect_format(), _parse_groups(), _parse_question(), parse_quiz_report(), _parse_settings(), _parse_summary(), parse_summary_from_xml() (+23 more)

### Community 2 - "EmailForwarder"
Cohesion: 0.09
Nodes (20): EmailForwarder, __init__(), main(), Парсит HTML письма и извлекает структурированные данные Args: html_body: HTML…, Выводит User ID в консоль Args: user_id: User ID для вывода subject: Тема…, Находит студента в базе данных по коду с загрузкой группы и кураторов Args:…, Находит кураторов группы студента Args: student: Объект Student Returns: Список…, Получает email кураторов группы студента с включённым флагом send_emails Args:… (+12 more)

### Community 3 - "story_llm.py"
Cohesion: 0.08
Nodes (35): Agent, check_retelling_audio(), _build_user_prompt(), check_sentence_rubric(), check_vocab_rubric(), _count_sentences(), _get_agent(), _is_optional_vocab_nag() (+27 more)

### Community 4 - "test_dictation.py"
Cohesion: 0.15
Nodes (10): choose_words(), grade_answer(), DictationAudioCueTests, DictationGradingTests, NovgorodDictationTests, PairDictationSingularAudioTests, PluralDictationGradingTests, SimpleTestCase (+2 more)

### Community 5 - "Student"
Cohesion: 0.13
Nodes (10): require_GET, Локальная страница запуска с фиксированной тестовой личностью., test_launcher(), django_db, Migration, Migration, Student, Migration (+2 more)

### Community 6 - "api/views.py"
Cohesion: 0.05
Nodes (60): check_story(), _is_usable_task_code(), _persist_reading_attempt(), _persist_speaking_attempt(), _persist_story_attempt(), csrf_exempt, require_POST, quiz_result() (+52 more)

### Community 7 - "register"
Cohesion: 0.11
Nodes (15): CourseAdmin, LessonAdmin, register, Возвращает количество уроков в курсе., Админ-интерфейс для модели Lesson., Возвращает количество заданий в уроке., Админ-интерфейс для модели Task., Возвращает количество попыток выполнения задания. (+7 more)

### Community 8 - "email_forwarder.py"
Cohesion: 0.05
Nodes (39): AbstractUser, BaseUserAdmin, django_contrib_auth_admin, django_contrib_auth_models, django_contrib_auth_validators, django_utils_timezone, email, email_header (+31 more)

### Community 9 - "django_conf"
Cohesion: 0.09
Nodes (11): Раздача HTML-уроков из каталога tasks/ по HTTP (не file://)., Отдаёт безопасные файлы из tasks/ (html/js/css), включая вложенные каталоги., serve_task_file(), URL configuration for russ_lang project., django_conf, django_conf_urls_static, django_http, django_urls (+3 more)

### Community 10 - "GroupResultsView"
Cohesion: 0.17
Nodes (8): GroupResultsView, MyGroupsView, LoginRequiredMixin, TemplateView, Представление для отображения детальных результатов урока студента., Представление для отображения групп пользователя. Для обычных пользователей:…, Представление для отображения результатов группы по курсам., StudentLessonResultsView

### Community 11 - "User Management Template"
Cohesion: 0.13
Nodes (17): Student Remove Confirm Template, Soft Remove From Group, Admin Panel Template, Admin Panel Stub, Password Reset Complete Template, Password Reset Confirm Template, Password Reset Done Template, Password Reset Email Template (+9 more)

### Community 12 - "UserForm"
Cohesion: 0.18
Nodes (8): django, django_contrib_auth, django_contrib_auth_forms, Meta, ProfileEditForm, Форма для создания и редактирования пользователя администратором., Форма для редактирования данных профиля пользователя., UserForm

### Community 13 - "Quiz Report Question Header Partial"
Cohesion: 0.20
Nodes (15): Quiz Report Groups Partial, Quiz Report Question Header Partial, Quiz Report Summary Partial, Quiz Report Text Content Partial, Multiple Response Question Template, Numeric Question Template, Numeric Acceptable Answer Rules, Sequence Question Template (+7 more)

### Community 14 - ".form_valid"
Cohesion: 0.18
Nodes (6): PasswordResetConfirmView, PasswordResetView, CustomPasswordResetConfirmView, CustomPasswordResetView, Представление для установки нового пароля., Представление для запроса сброса пароля.

### Community 15 - "ADDED Requirements"
Cohesion: 0.14
Nodes (13): ADDED Requirements, Purpose, Requirement: Client sends identity and task code, Requirement: Persist story check as task attempt, Requirement: Soft-fail persistence, Scenario: Completion record when check ok, Scenario: Missing student code, Scenario: Payload includes student and task codes (+5 more)

### Community 16 - "reading_check.py"
Cohesion: 0.06
Nodes (40): align_reference_to_words(), check_reading_audio(), coverage_ratio(), period_boundary_token_indices(), Any, Greedy sequential alignment: for each reference token, find the next ASR word…, Split on sentence-ending periods; keep non-empty trimmed sentences., For each sentence that ends with '.' and has a following sentence, return the… (+32 more)

### Community 17 - "import_students.py"
Cohesion: 0.29
Nodes (6): Command, group_code_from_name(), normalize(), parse_curator_name(), BaseCommand, username_from_email()

### Community 18 - "base.html Layout"
Cohesion: 0.29
Nodes (11): base.html Layout, Group Confirm Delete Template, Non-Empty Group Delete Guard, Group Form Template, Group Form Fields (name, code, curators), Group Management Template, Group Results Template, Group Students Template (+3 more)

### Community 19 - "Quiz Question Status Header"
Cohesion: 0.29
Nodes (11): Quiz Question Body Dynamic Include, Quiz Question Status Header, Quiz Text Content Blocks, dndQuestion, essayQuestion, fillInTheBlankQuestion, hotspotQuestion, likertScaleQuestion (+3 more)

### Community 20 - "GroupAdmin"
Cohesion: 0.20
Nodes (7): GroupAdmin, register, Админ-интерфейс для модели Group., Возвращает список кураторов через запятую., Возвращает количество студентов в группе., Админ-интерфейс для модели Student., StudentAdmin

### Community 21 - "dictation_views.py"
Cohesion: 0.17
Nodes (19): public_state(), Диктант AI_3_7: фиксированный эталон, случайный набор и прозрачные баллы., run_score(), answer(), _body(), _find_session(), atomic, csrf_exempt (+11 more)

### Community 22 - "test_ai_test_launcher.py"
Cohesion: 0.18
Nodes (9): courses_course_sync, Course, Meta, Модель задания студента (завершенное задание)., StudentTask, django_core_management, django_core_management_base, django_test (+1 more)

### Community 23 - "TaskAttempt"
Cohesion: 0.13
Nodes (12): Command, atomic, BaseCommand, Модель попытки выполнения задания., TaskAttempt, Capabilities, Impact, Modified Capabilities (+4 more)

### Community 24 - "dictation.js"
Cohesion: 0.42
Nodes (9): begin(), el(), feedbackText(), renderSummary(), request(), showCurrent(), storeRun(), studentCode() (+1 more)

### Community 25 - "UserUpdateView"
Cohesion: 0.20
Nodes (6): ListView, UserPassesTestMixin, Главная страница управления пользователями со списком всех пользователей.…, Представление для редактирования пользователя., UserManagementView, UserUpdateView

### Community 26 - "GroupUpdateView"
Cohesion: 0.22
Nodes (6): GroupForm, Meta, Форма для создания и редактирования группы., GroupUpdateView, UpdateView, Представление для редактирования группы.

### Community 27 - "Урок 4"
Cohesion: 0.04
Nodes (45): Выполненный запуск, Исключённый дубль, Коды ИИ-заданий, Подключение к PostgreSQL, Подключение через SSH, Создание курса русского языка, 10. 2.4.1 Рассказ «Мой университет», 11. 2.16 Чтение текста «Москва — столица» (+37 more)

### Community 29 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+17 more)

### Community 31 - "deploy.sh"
Cohesion: 0.83
Nodes (3): die(), log(), deploy.sh script

### Community 32 - "PluralDictationAPITests"
Cohesion: 0.28
Nodes (5): NovgorodDictationAPITests, PluralDictationAPITests, override_settings, TestCase, SingularPluralAPITests

### Community 33 - "Student Lesson Results Template"
Cohesion: 0.50
Nodes (4): Student Lesson Results Template, Attempt Results Modal, render_attempt_results Tag, Task Name Search Filter

### Community 34 - "LoginRequiredMixin"
Cohesion: 0.29
Nodes (6): AdminPanelView, ProfileView, LoginRequiredMixin, TemplateView, Главная страница профиля пользователя с вкладками., Страница-заглушка для администрирования. Доступна только для пользователей с…

### Community 35 - "ADDED Requirements"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Purpose, Requirement: Lesson 3 reading task UI, Requirement: Persist completed reading attempt, Requirement: Reading check does not score stress or enumeration intonation, Requirement: Reading check evaluates coverage, duration, and period pauses, Scenario: Attempt saved on complete, Scenario: Incomplete coverage fails the check (+7 more)

### Community 36 - "students/views.py"
Cohesion: 0.14
Nodes (13): django_contrib_auth_decorators, django_contrib_auth_mixins, django_contrib_auth_views, django_db_models, login_required, LoginView, LogoutView, CustomLoginView (+5 more)

### Community 37 - "opsx-explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 38 - "forwarder/apps.py"
Cohesion: 0.14
Nodes (10): ApiConfig, AppConfig, django_apps, ForwarderConfig, AppConfig, AppConfig, StudentsConfig, threading (+2 more)

### Community 39 - "generate_yandex_dictation_audio.py"
Cohesion: 0.06
Nodes (37): argparse, array, base64, Явный профиль БД из .env для синхронизации курса; локальный сервер не…, Django settings for russ_lang project., django_core_exceptions, dotenv, hashlib (+29 more)

### Community 40 - "RemoveStudentFromGroupView"
Cohesion: 0.23
Nodes (5): GroupDeleteView, DeleteView, Представление для удаления группы., Представление для удаления студента из группы (установка group=None)., RemoveStudentFromGroupView

### Community 41 - "test_api_config.cjs"
Cohesion: 0.20
Nodes (9): ref_node_assert_strict, ref_node_fs, ref_node_path, ref_node_vm, assert, fs, path, script (+1 more)

### Community 42 - "os"
Cohesion: 0.29
Nodes (5): ASGI config for russ_lang project. It exposes the ASGI callable as a module-…, WSGI config for russ_lang project. It exposes the WSGI callable as a module-…, django_core_asgi, django_core_wsgi, os

### Community 43 - ".agents/skills/openspec-explore/SKILL.md"
Cohesion: 0.25
Nodes (7): Ending Discovery, Guardrails, Handling Different Entry Points, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do

### Community 44 - "Task"
Cohesion: 0.17
Nodes (9): collections, Command, BaseCommand, Command, BaseCommand, Lesson, Task, openpyxl (+1 more)

### Community 45 - "Requirement: Persist attempt only after three successful words"
Cohesion: 0.13
Nodes (14): ADDED Requirements, Purpose, Requirement: Persist attempt only after three successful words, Requirement: Return check result to frontend, Requirement: Transcribe speaking audio via Nexara, Scenario: Frontend advances on ok, Scenario: Missing audio or reference, Scenario: Nexara failure (+6 more)

### Community 46 - "ProfileEditView"
Cohesion: 0.20
Nodes (6): ProfileEditView, DeleteView, UpdateView, Представление для удаления пользователя., Представление для редактирования данных профиля., UserDeleteView

### Community 47 - "ADDED Requirements"
Cohesion: 0.20
Nodes (9): ADDED Requirements, Purpose, Requirement: Reject unsafe task paths, Requirement: Serve nested task static files, Scenario: Disallowed extension is blocked, Scenario: Flat task file still works, Scenario: Nested HTML is available, Scenario: Path traversal is blocked (+1 more)

### Community 48 - "Задания"
Cohesion: 0.20
Nodes (9): Задания, Локальная проверка, Пробная озвучка Yandex SpeechKit, Текущая озвучка всех диктантов — Yandex SpeechKit, Ударения в озвучке диктантов, Урок 1, Урок 2, Урок 3 (+1 more)

### Community 49 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 50 - "users/views.py"
Cohesion: 0.17
Nodes (10): django_contrib, django_shortcuts, django_utils_crypto, django_views_generic, PasswordResetCompleteView, PasswordResetDoneView, CustomPasswordResetCompleteView, CustomPasswordResetDoneView (+2 more)

### Community 57 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 59 - ".cursor/skills/openspec-explore/SKILL.md"
Cohesion: 0.25
Nodes (7): Ending Discovery, Guardrails, Handling Different Entry Points, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do

### Community 70 - "update_prod.sh"
Cohesion: 0.48
Nodes (5): log_error(), log_info(), read_env_value(), update_prod.sh script, usage()

### Community 71 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 72 - "course_sync.py"
Cohesion: 0.23
Nodes (10): apply_plan(), build_plan(), DesiredTask, Добавление курса и заданий без очистки таблиц и потери результатов., read_regular_tasks(), SyncPlan, Command, BaseCommand (+2 more)

### Community 73 - "GroupCreateView"
Cohesion: 0.33
Nodes (3): GroupCreateView, CreateView, Представление для создания новой группы.

### Community 74 - "AITestLauncherTests"
Cohesion: 0.20
Nodes (3): AITestLauncherTests, override_settings, TestCase

### Community 76 - "GroupManagementView"
Cohesion: 0.22
Nodes (6): GroupManagementView, GroupStudentsView, ListView, UserPassesTestMixin, Главная страница управления группами со списком всех групп. Доступна только для…, Представление для просмотра списка студентов группы и управления ими.

### Community 77 - "courses/migrations/0001_initial.py"
Cohesion: 0.40
Nodes (3): Migration, django_db_models_deletion, Migration

### Community 78 - "ProfilePasswordChangeView"
Cohesion: 0.40
Nodes (3): PasswordChangeView, ProfilePasswordChangeView, Представление для изменения пароля пользователя.

### Community 79 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 80 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 81 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 82 - "Group"
Cohesion: 0.40
Nodes (3): Group, Meta, Модель группы студентов.

### Community 96 - "OpenSpec Awareness"
Cohesion: 0.50
Nodes (4): Check for context, OpenSpec Awareness, When a change exists, When no change exists

### Community 98 - "UserCreateView"
Cohesion: 0.40
Nodes (3): CreateView, Представление для создания нового пользователя., UserCreateView

### Community 99 - "Command"
Cohesion: 0.50
Nodes (3): Command, atomic, BaseCommand

### Community 100 - "OpenSpec Awareness"
Cohesion: 0.50
Nodes (4): Check for context, OpenSpec Awareness, When a change exists, When no change exists

### Community 104 - ".get_context_data"
Cohesion: 0.36
Nodes (5): AdminPasswordChangeForm, Форма для смены пароля пользователя администратором. Использует встроенную…, UserPasswordChangeForm, Представление для смены пароля пользователя администратором., UserPasswordChangeView

### Community 106 - "Проверка ударений в диктантах"
Cohesion: 0.33
Nodes (5): dictation_1, dictation_2, Исправление разметки Microsoft IPA, Проверка ударений в диктантах, Текущая озвучка SpeechKit

## Ambiguous Edges - Review These
- `students:my_groups` → `Quiz Report Group Results`  [AMBIGUOUS]
  students/templates/quiz_report/_groups.html · relation: conceptually_related_to

## Knowledge Gaps
- **210 isolated node(s):** `Migration`, `assert`, `fs`, `path`, `vm` (+205 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 526 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `students:my_groups` and `Quiz Report Group Results`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `TaskAttempt` connect `TaskAttempt` to `PluralDictationAPITests`, `ADDED Requirements`, `test_dictation.py`, `Student`, `api/views.py`, `students/views.py`, `AITestLauncherTests`, `CourseSyncTests`, `GroupResultsView`, `Requirement: Persist attempt only after three successful words`, `ADDED Requirements`, `import_students.py`, `test_ai_test_launcher.py`, `Proposal`, `DictationAPITests`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `Student` connect `Student` to `EmailForwarder`, `Command`, `students/views.py`, `api/views.py`, `email_forwarder.py`, `RemoveStudentFromGroupView`, `AITestLauncherTests`, `CourseSyncTests`, `GroupResultsView`, `import_students.py`, `Group`, `test_ai_test_launcher.py`, `TaskAttempt`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `EmailForwarder` connect `EmailForwarder` to `email_forwarder.py`, `.ready`, `Student`, `forwarder/apps.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `TaskAttempt` (e.g. with `DictationAPITests` and `NovgorodDictationAPITests`) actually correct?**
  _`TaskAttempt` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `assert`, `fs` to the rest of the system?**
  _210 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `find_child` be split into smaller, more focused modules?**
  _Cohesion score 0.14111261872455902 - nodes in this community are weakly interconnected._