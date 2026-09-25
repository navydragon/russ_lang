# Graph Report - russ_lang  (2026-09-17)

## Corpus Check
- Corpus is ~23,669 words - fits in a single context window. You may not need a graph.

## Summary
- 578 nodes · 1092 edges · 71 communities (50 shown, 21 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Quiz Question Parsers
- Quiz Report Pipeline
- Email Forwarder
- Story LLM Check API
- Course Models Import
- Student Groups Model
- Quiz Result Services
- Courses Admin
- Setup Docs Templates
- Student Auth Forms
- Group Results Views
- User Admin Templates
- User Profile Forms
- Quiz Report Templates
- Password Reset Views
- Group Delete Views
- Custom User Admin
- Import Students Command
- Group UI Templates
- Quiz Question UI Partials
- Groups Admin
- Admin Password Change
- Story Task Frontends
- Profile Admin Views
- User Edit Views
- User Delete Views
- User Create Views
- User Management List
- Django Settings
- Manage.py Entrypoint
- Password Reset Request
- Deploy Script
- Curators M2M Migration
- Lesson Results Template
- API App Config
- Courses App Config
- Password Reset Done
- Students App Config
- Users App Config
- Tutor Flag Migration
- ASGI Config
- Root URL Config
- WSGI Config
- Courses Initial Migration
- Students Initial Migration
- Student Group Alter
- Student SID Migration
- Remove Student SID
- Users Initial Migration
- User Name Fields Alter
- Send Emails Flag
- CORS Headers Dependency
- Openpyxl Dependency
- Pydantic AI Dependency

## God Nodes (most connected - your core abstractions)
1. `find_child()` - 38 edges
2. `find_children()` - 34 edges
3. `parse_question_base()` - 34 edges
4. `register_question_parser()` - 29 edges
5. `element_text()` - 22 edges
6. `parse_text_with_equation()` - 21 edges
7. `parse_quiz_report()` - 19 edges
8. `EmailForwarder` - 18 edges
9. `Group` - 18 edges
10. `strip_ns()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Student Remove Confirm Template` --semantically_similar_to--> `User Confirm Delete Template`  [INFERRED] [semantically similar]
  students/templates/students/student_remove_confirm.html → users/templates/users/user_confirm_delete.html
- `GroupResultsView` --uses--> `Course`  [INFERRED]
  students/views.py → courses/models.py
- `GroupResultsView` --uses--> `Lesson`  [INFERRED]
  students/views.py → courses/models.py
- `StudentLessonResultsView` --uses--> `Lesson`  [INFERRED]
  students/views.py → courses/models.py
- `Command` --uses--> `StudentTask`  [INFERRED]
  students/management/commands/import_students.py → courses/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Email Provider Configuration Set** — readme_gmail_provider, readme_yandex_provider, readme_mailru_provider, readme_outlook_provider, readme_env_configuration [EXTRACTED 1.00]
- **Quiz Report Shared Partials** — students_templates_quiz_report__question_header_question_status, students_templates_quiz_report__text_content_text_blocks, students_templates_quiz_report__question_body_dynamic_include, students_templates_quiz_report__summary_report_summary, students_templates_quiz_report__groups_group_results [INFERRED 0.85]
- **Quiz Report Question Type Templates** — students_templates_quiz_report_questions_dndquestion_dnd, students_templates_quiz_report_questions_essayquestion_essay, students_templates_quiz_report_questions_fillintheblankquestion_fill_blank, students_templates_quiz_report_questions_hotspotquestion_hotspot, students_templates_quiz_report_questions_likertscalequestion_likert, students_templates_quiz_report_questions_matchingquestion_matching, students_templates_quiz_report_questions_multiplechoicequestion_mcq, students_templates_quiz_report_questions_multiplechoicetextquestion_mct [EXTRACTED 1.00]
- **Quiz Report Question Type Renderers** — students_templates_quiz_report_questions_multipleresponsequestion, students_templates_quiz_report_questions_numericquestion, students_templates_quiz_report_questions_sequencequestion, students_templates_quiz_report_questions_truefalsequestion, students_templates_quiz_report_questions_typeinquestion, students_templates_quiz_report_questions_unknown, students_templates_quiz_report_questions_wordbankquestion, students_templates_quiz_report__question_header [EXTRACTED 1.00]
- **Quiz Report Page Assembly** — students_templates_quiz_report_report, students_templates_quiz_report__summary, students_templates_quiz_report__groups, students_templates_quiz_report_report_render_question [EXTRACTED 1.00]
- **Student Group Management UI** — students_templates_students_group_management, students_templates_students_group_form, students_templates_students_group_students, students_templates_students_group_confirm_delete, students_templates_students_my_groups, students_templates_students_group_results [INFERRED 0.85]
- **Password Reset Flow** — users_templates_users_password_reset_subject, users_templates_users_password_reset_email, users_templates_users_password_reset_done, users_templates_users_password_reset_confirm, users_templates_users_password_reset_complete [INFERRED 0.85]
- **AI Story Check Tasks** — tasks_family_story, tasks_room_story, tasks_family_story_api_story_check, tasks_room_story_api_story_check [INFERRED 0.95]
- **User Management CRUD UI** — users_templates_users_user_management, users_templates_users_user_form, users_templates_users_user_confirm_delete, users_templates_users_user_password_change [INFERRED 0.85]

## Communities (71 total, 21 thin omitted)

### Community 0 - "Quiz Question Parsers"
Cohesion: 0.15
Nodes (45): parse_dnd(), _parse_objects(), _parse_placements(), Element, parse_essay(), Element, parse_fill_in_blank(), Element (+37 more)

### Community 1 - "Quiz Report Pipeline"
Cohesion: 0.09
Nodes (26): detect_format(), _parse_groups(), _parse_question(), parse_quiz_report(), _parse_settings(), _parse_summary(), parse_summary_from_xml(), Element (+18 more)

### Community 2 - "Email Forwarder"
Cohesion: 0.08
Nodes (22): ForwarderConfig, AppConfig, Запускает email_forwarder в отдельном потоке при старте Django. Запускается…, EmailForwarder, main(), Парсит HTML письма и извлекает структурированные данные Args: html_body: HTML…, Выводит User ID в консоль Args: user_id: User ID для вывода subject: Тема…, Находит студента в базе данных по коду с загрузкой группы и кураторов Args:… (+14 more)

### Community 3 - "Story LLM Check API"
Cohesion: 0.13
Nodes (28): Agent, _build_user_prompt(), check_sentence_rubric(), check_story(), check_vocab_rubric(), _count_sentences(), _get_agent(), _is_optional_vocab_nag() (+20 more)

### Community 4 - "Course Models Import"
Cohesion: 0.14
Nodes (12): Command, BaseCommand, Command, BaseCommand, Course, Lesson, Meta, Модель попытки выполнения задания. (+4 more)

### Community 5 - "Student Groups Model"
Cohesion: 0.11
Nodes (13): Group, Meta, Модель группы студентов., GroupCreateView, GroupManagementView, GroupUpdateView, CreateView, ListView (+5 more)

### Community 6 - "Quiz Result Services"
Cohesion: 0.18
Nodes (14): extract_score_percent(), extract_score_value(), _find_student(), parse_russian_date(), Any, Парсит дату из русского формата в datetime объект. Примеры форматов: - "22…, Сохраняет результат выполнения задания в базу данных. Args: parsed_data:…, Извлекает процент из строки score. Примеры: - "10 / 10 (100%)" -> 100.00 - "5 /… (+6 more)

### Community 7 - "Courses Admin"
Cohesion: 0.11
Nodes (15): CourseAdmin, LessonAdmin, register, Возвращает количество уроков в курсе., Админ-интерфейс для модели Lesson., Возвращает количество заданий в уроке., Админ-интерфейс для модели Task., Возвращает количество попыток выполнения задания. (+7 more)

### Community 8 - "Setup Docs Templates"
Cohesion: 0.13
Nodes (19): App Password, AUTO_START_EMAIL_FORWARDER, email_forwarder.py, Email Forwarding Script, .env Configuration, Gmail Provider Setup, IMAP/SMTP Real-time Monitoring, Mail.ru Provider Setup (+11 more)

### Community 9 - "Student Auth Forms"
Cohesion: 0.12
Nodes (12): login_required, LoginView, LogoutView, GroupForm, Meta, Форма для создания и редактирования группы., CustomLoginView, CustomLogoutView (+4 more)

### Community 10 - "Group Results Views"
Cohesion: 0.15
Nodes (10): GroupResultsView, GroupStudentsView, MyGroupsView, LoginRequiredMixin, TemplateView, Представление для отображения детальных результатов урока студента., Представление для отображения групп пользователя. Для обычных пользователей:…, Представление для просмотра списка студентов группы и управления ими. (+2 more)

### Community 11 - "User Admin Templates"
Cohesion: 0.13
Nodes (17): Student Remove Confirm Template, Soft Remove From Group, Admin Panel Template, Admin Panel Stub, Password Reset Complete Template, Password Reset Confirm Template, Password Reset Done Template, Password Reset Email Template (+9 more)

### Community 12 - "User Profile Forms"
Cohesion: 0.16
Nodes (8): PasswordResetCompleteView, Meta, ProfileEditForm, Форма для создания и редактирования пользователя администратором., Форма для редактирования данных профиля пользователя., UserForm, CustomPasswordResetCompleteView, Представление для подтверждения успешного сброса пароля.

### Community 13 - "Quiz Report Templates"
Cohesion: 0.20
Nodes (15): Quiz Report Groups Partial, Quiz Report Question Header Partial, Quiz Report Summary Partial, Quiz Report Text Content Partial, Multiple Response Question Template, Numeric Question Template, Numeric Acceptable Answer Rules, Sequence Question Template (+7 more)

### Community 14 - "Password Reset Views"
Cohesion: 0.17
Nodes (6): PasswordChangeView, PasswordResetConfirmView, CustomPasswordResetConfirmView, ProfilePasswordChangeView, Представление для установки нового пароля., Представление для изменения пароля пользователя.

### Community 15 - "Group Delete Views"
Cohesion: 0.23
Nodes (5): GroupDeleteView, DeleteView, Представление для удаления группы., Представление для удаления студента из группы (установка group=None)., RemoveStudentFromGroupView

### Community 16 - "Custom User Admin"
Cohesion: 0.20
Nodes (8): AbstractUser, BaseUserAdmin, register, Админ-интерфейс для кастомной модели пользователя., UserAdmin, Meta, Кастомная модель пользователя с дополнительными полями: - Фамилия (last_name) -…, User

### Community 17 - "Import Students Command"
Cohesion: 0.25
Nodes (6): Command, group_code_from_name(), normalize(), parse_curator_name(), BaseCommand, username_from_email()

### Community 18 - "Group UI Templates"
Cohesion: 0.29
Nodes (11): base.html Layout, Group Confirm Delete Template, Non-Empty Group Delete Guard, Group Form Template, Group Form Fields (name, code, curators), Group Management Template, Group Results Template, Group Students Template (+3 more)

### Community 19 - "Quiz Question UI Partials"
Cohesion: 0.29
Nodes (11): Quiz Question Body Dynamic Include, Quiz Question Status Header, Quiz Text Content Blocks, dndQuestion, essayQuestion, fillInTheBlankQuestion, hotspotQuestion, likertScaleQuestion (+3 more)

### Community 20 - "Groups Admin"
Cohesion: 0.20
Nodes (7): GroupAdmin, register, Админ-интерфейс для модели Group., Возвращает список кураторов через запятую., Возвращает количество студентов в группе., Админ-интерфейс для модели Student., StudentAdmin

### Community 21 - "Admin Password Change"
Cohesion: 0.31
Nodes (6): AdminPasswordChangeForm, Форма для смены пароля пользователя администратором. Использует встроенную…, UserPasswordChangeForm, UserPassesTestMixin, Представление для смены пароля пользователя администратором., UserPasswordChangeView

### Community 22 - "Story Task Frontends"
Cohesion: 0.39
Nodes (8): Family Story Task UI, Story Check API Client, Error Span Highlighting, TASK_ID family, Room Story Task UI, Story Check API Client, Error Span Highlighting, TASK_ID room

### Community 23 - "Profile Admin Views"
Cohesion: 0.29
Nodes (6): AdminPanelView, ProfileView, LoginRequiredMixin, TemplateView, Главная страница профиля пользователя с вкладками., Страница-заглушка для администрирования. Доступна только для пользователей с…

### Community 24 - "User Edit Views"
Cohesion: 0.25
Nodes (5): ProfileEditView, UpdateView, Представление для редактирования пользователя., Представление для редактирования данных профиля., UserUpdateView

### Community 25 - "User Delete Views"
Cohesion: 0.33
Nodes (3): DeleteView, Представление для удаления пользователя., UserDeleteView

### Community 26 - "User Create Views"
Cohesion: 0.40
Nodes (3): CreateView, Представление для создания нового пользователя., UserCreateView

### Community 27 - "User Management List"
Cohesion: 0.40
Nodes (3): ListView, Главная страница управления пользователями со списком всех пользователей.…, UserManagementView

### Community 29 - "Manage.py Entrypoint"
Cohesion: 0.67
Nodes (3): _inject_default_runserver_port(), main(), Run administrative tasks.

### Community 30 - "Password Reset Request"
Cohesion: 0.50
Nodes (3): PasswordResetView, CustomPasswordResetView, Представление для запроса сброса пароля.

### Community 31 - "Deploy Script"
Cohesion: 0.83
Nodes (3): die(), log(), deploy.sh script

### Community 33 - "Lesson Results Template"
Cohesion: 0.50
Nodes (4): Student Lesson Results Template, Attempt Results Modal, render_attempt_results Tag, Task Name Search Filter

### Community 36 - "Password Reset Done"
Cohesion: 0.67
Nodes (3): PasswordResetDoneView, CustomPasswordResetDoneView, Представление для подтверждения отправки письма со ссылкой для сброса пароля.

## Ambiguous Edges - Review These
- `students:my_groups` → `Quiz Report Group Results`  [AMBIGUOUS]
  students/templates/quiz_report/_groups.html · relation: conceptually_related_to

## Knowledge Gaps
- **37 isolated node(s):** `Migration`, `Meta`, `Migration`, `Migration`, `Migration` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `students:my_groups` and `Quiz Report Group Results`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `parse_summary_from_xml()` connect `Quiz Report Pipeline` to `Quiz Result Services`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `Student` connect `Quiz Result Services` to `Email Forwarder`, `Course Models Import`, `Student Groups Model`, `Student Auth Forms`, `Group Results Views`, `Group Delete Views`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `save_quiz_result()` connect `Quiz Result Services` to `Email Forwarder`, `Story LLM Check API`, `Course Models Import`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `Migration`, `Meta`, `Migration` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Quiz Report Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.08880666049953746 - nodes in this community are weakly interconnected._
- **Should `Email Forwarder` be split into smaller, more focused modules?**
  _Cohesion score 0.08108108108108109 - nodes in this community are weakly interconnected._