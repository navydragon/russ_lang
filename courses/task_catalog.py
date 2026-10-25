"""Каталог ИИ-заданий для локальных тестовых данных и страницы запуска."""
from dataclasses import dataclass


TEST_COURSE_NAME = 'Русский язык — тестовый курс ИИ'
TEST_GROUP_CODE = 'AI_TEST_GROUP'
TEST_STUDENT_CODE = 'AI_TEST_STUDENT'
# Удалённый дубль не получает нового значения и не используется повторно.
RETIRED_AI_CODES = frozenset({'AI_3_3'})


@dataclass(frozen=True)
class TaskDefinition:
    number: int
    lesson: int
    position: int
    legacy_code: str
    name: str
    source_number: str = ''
    html_path: str = ''

    @property
    def code(self):
        return f'AI_{self.lesson}_{self.position}'


TASK_CATALOG = (
    TaskDefinition(1, 1, 1, 'family_story', 'Рассказ «Семья»', html_path='lesson1/family_story/family_story.html'),
    TaskDefinition(2, 1, 2, 'room_story', 'Рассказ «Комната»', html_path='lesson1/room_story/room_story.html'),
    TaskDefinition(3, 1, 3, 'city_speaking', 'Говорение «Город»', html_path='lesson1/city_speaking/city_speaking.html'),
    TaskDefinition(4, 1, 4, 'class_speaking', 'Говорение «Класс»', html_path='lesson1/class_speaking/class_speaking.html'),
    TaskDefinition(5, 1, 5, 'flat_speaking', 'Говорение «Квартира»', html_path='lesson1/flat_speaking/flat_speaking.html'),
    TaskDefinition(6, 2, 1, 'photo_album_reading', 'Чтение «Мой фотоальбом»', '2.2', 'lesson2/photo_album_reading/photo_album_reading.html'),
    TaskDefinition(7, 2, 2, 'family_retelling', 'Рассказ о своей семье по фотографии', '2.4', 'lesson2/family_retelling/family_retelling.html'),
    TaskDefinition(8, 3, 1, 'university_reading', 'Чтение «Наш университет»', '2.1', 'lesson3/university_reading/university_reading.html'),
    TaskDefinition(9, 3, 2, 'university_retelling', 'Пересказ «Наш университет» по опорам', '2.2.1', 'lesson3/university_retelling/university_retelling.html'),
    TaskDefinition(10, 3, 4, 'my_university_story', 'Рассказ «Мой университет»', '2.4.1', 'lesson3/my_university_story/my_university_story.html'),
    TaskDefinition(11, 3, 5, 'moscow_reading', 'Чтение «Москва — столица»', '2.16', 'lesson3/moscow_reading/moscow_reading.html'),
    TaskDefinition(12, 3, 6, 'moscow_retelling', 'Пересказ «Москва — столица»', '2.18.1', 'lesson3/moscow_retelling/moscow_retelling.html'),
    TaskDefinition(13, 3, 7, 'lesson3_dictation_1', 'Диктант № 1', '3.2.1', 'lesson3/dictation_1/dictation_1.html'),
    TaskDefinition(14, 3, 8, 'lesson3_dictation_2', 'Диктант № 2', '3.2.1', 'lesson3/dictation_2/dictation_2.html'),
    TaskDefinition(15, 3, 9, 'lesson3_dictation_words', 'Диктант № 3 со списком слов', html_path='lesson3/dictation_3/dictation_3.html'),
    TaskDefinition(16, 3, 10, 'novgorod_dictation', 'Диктант с текстом о Новгороде', '3.4', 'lesson3/novgorod_dictation/novgorod_dictation.html'),
    TaskDefinition(17, 3, 11, 'novgorod_retelling', 'Пересказ «Новгород»', '3.4.1', 'lesson3/novgorod_retelling/novgorod_retelling.html'),
    TaskDefinition(18, 4, 1, 'lesson4_university_reading', 'Чтение «Мой университет»', '3.1 и 3.2'),
    TaskDefinition(19, 4, 2, 'lesson4_university_writing', 'Письменная работа «Мой университет»', '3.4.1'),
    TaskDefinition(20, 4, 3, 'lesson4_university_questions', 'Вопросы к тексту об университете', '3.7.1'),
    TaskDefinition(21, 4, 4, 'lesson4_university_retelling', 'Письменный пересказ «Наш университет»', '3.8.1'),
    TaskDefinition(22, 4, 5, 'neighborhood_reading', 'Чтение «Наш район и наша улица»', '3.15.1'),
    TaskDefinition(23, 4, 6, 'lesson4_family_story', 'Сочинение «Моя семья»', '3.19.1'),
    TaskDefinition(24, 4, 7, 'lesson4_dialogue_1', 'Чтение диалога', '4.1'),
    TaskDefinition(25, 4, 8, 'lesson4_text_answer', 'Ответ по тексту', '4.2.1'),
    TaskDefinition(26, 4, 9, 'lesson4_dialogue_3', 'Чтение диалога', '4.3'),
    TaskDefinition(27, 4, 10, 'lesson4_dialogue_4', 'Чтение диалога', '4.4'),
    TaskDefinition(28, 4, 11, 'lesson4_written_answer', 'Письменный ответ', '4.5.1'),
    TaskDefinition(29, 4, 12, 'library_retelling', 'Изложение «Наша библиотека»', '5.5'),
    TaskDefinition(30, 4, 13, 'ivan_retelling', 'Изложение «Мой друг Иван»', '5.7 / 5.7.1'),
    TaskDefinition(31, 4, 14, 'lesson4_final_check', 'Итоговый контроль ИИ'),
)
