"""Диктант AI_3_7: фиксированный эталон, случайный набор и прозрачные баллы."""
import re
import secrets


TASK_CODE = 'AI_3_7'
WORD_COUNT = 10
PASSING_SCORE = 60

# Голос произносит только существительное; студент самостоятельно дописывает местоимение.
ANSWERS = (
    'мой класс', 'мой завод', 'мой урок', 'моя машина', 'моя книга',
    'мой учебник', 'мой журнал', 'мой вопрос', 'моя газета', 'мой глагол',
    'моя ошибка', 'моя ручка', 'моя тетрадь', 'моя девочка', 'моя девушка',
    'мой мальчик', 'мой преподаватель', 'мой студент', 'моя студентка',
    'мой фильм', 'мой магазин', 'моя фабрика', 'мой парк', 'моя буква', 'мой звук',
)
WORDS = tuple({'id': i, 'pronoun': a.split()[0], 'noun': a.split()[1], 'answer': a} for i, a in enumerate(ANSWERS, 1))


PAIR_ANSWERS = (
    'лампы и карандаши', 'радио и газеты', 'учебники и дни', 'шкафы и карты',
    'портфели и тетради', 'пальто и костюмы', 'папки и словари', 'дома и общежития',
    'кровати и окна', 'журналы и картины', 'слова и упражнения', 'книги и места',
    'машины и телевизоры', 'братья и отцы', 'матери и друзья',
    'сёстры и товарищи', 'дочери и преподаватели',
)
SINGULAR_WORDS = (
    'друг', 'брат', 'стул', 'человек', 'ребёнок', 'дом', 'поезд',
    'вечер', 'профессор', 'город', 'год', 'день', 'отец', 'мать',
    'дочь', 'дерево', 'метро', 'радио', 'пальто', 'бюро', 'такси',
)
PLURAL_ANSWERS = (
    'друзья', 'братья', 'стулья', 'люди', 'дети', 'дома', 'поезда',
    'вечера', 'профессора', 'города', 'года', 'дни', 'отцы', 'матери',
    'дочери', 'деревья', 'метро', 'радио', 'пальто', 'бюро', 'такси',
)
NOVGOROD_SENTENCES = ('Я студент.', 'Я историк.', 'История – самая интересная наука.', 'Мой родной город Новгород.', 'Это небольшой город, но очень красивый.', 'Исторический центр города – Кремль, площадь, музей.', 'Моя семья здесь.', 'Мой отец экскурсовод.', 'А это наш дом и наша улица.', 'Здесь есть хорошие магазины и красивый парк.')
NOVGOROD_WORD_COUNT = sum(len(re.findall(r"\w+", sentence)) for sentence in NOVGOROD_SENTENCES)

TASKS = {
    'AI_3_10': {'count': len(NOVGOROD_SENTENCES), 'directory': 'novgorod_dictation', 'answers': NOVGOROD_SENTENCES},
    'AI_3_9': {'count': 10, 'directory': 'dictation_3', 'answers': PLURAL_ANSWERS},
    'AI_3_7': {'count': 10, 'directory': 'dictation_1', 'answers': ANSWERS},
    'AI_3_8': {'count': 5, 'directory': 'dictation_2', 'answers': PAIR_ANSWERS},
}

def choose_words(task_code=TASK_CODE):
    config = TASKS[task_code]
    if task_code == 'AI_3_10':
        return list(range(1, config['count'] + 1))
    return secrets.SystemRandom().sample(range(1, len(config['answers']) + 1), config['count'])

def grade_answer(word_id, answer, task_code=TASK_CODE):
    if task_code == 'AI_3_10':
        expected = NOVGOROD_SENTENCES[word_id - 1]
        normalize = lambda text: re.findall(r'\w+', text.casefold().replace('ё', 'е'), re.UNICODE)
        target, actual = normalize(expected), normalize(answer)
        # Levenshtein distance by words: insertions, omissions and substitutions cost one word.
        previous = list(range(len(actual) + 1))
        for i, token in enumerate(target, 1):
            current = [i]
            for j, other in enumerate(actual, 1):
                current.append(min(current[-1] + 1, previous[j] + 1, previous[j-1] + (token != other)))
            previous = current
        errors = previous[-1]
        credited = max(0, len(target) - errors)
        return {'word_id': word_id, 'answer': answer, 'expected': expected,
                'word_count': len(target), 'correct_words': credited, 'word_errors': errors,
                'score': round(100 * credited / NOVGOROD_WORD_COUNT, 2)}
    if task_code == 'AI_3_9':
        expected = PLURAL_ANSWERS[word_id - 1]
        tokens = re.findall(r'\w+', answer.casefold().replace('ё', 'е'), re.UNICODE)
        accepted = {expected}
        if expected == 'года':
            accepted.add('годы')  # Both nominative plural forms are standard Russian.
        score = 10 if len(tokens) == 1 and tokens[0] in accepted else 0
        return {'word_id': word_id, 'answer': answer, 'expected': expected,
                'singular': SINGULAR_WORDS[word_id - 1], 'score': score}
    if task_code == 'AI_3_8':
        expected = PAIR_ANSWERS[word_id - 1]
        first, second = expected.casefold().replace('ё', 'е').split(' и ')
        tokens = re.findall(r'\w+', answer.casefold().replace('ё', 'е'), re.UNICODE)
        if len(tokens) == 3 and tokens[1] == 'и':
            tokens = [tokens[0], tokens[2]]
        first_points = 10 if (len(tokens) in (1, 2) and tokens[0] == first) else 0
        second_points = 10 if (len(tokens) in (1, 2) and tokens[-1] == second) else 0
        return {'word_id': word_id, 'answer': answer, 'expected': expected,
                'first_points': first_points, 'second_points': second_points,
                'score': first_points + second_points}

    expected = WORDS[word_id - 1]
    tokens = re.findall(r'\w+', answer.casefold().replace('ё', 'е'), re.UNICODE)
    # Одно существительное или одно местоимение также может получить свои 5 баллов.
    noun = tokens[-1] if len(tokens) in (1, 2) else ''
    pronoun = tokens[0] if len(tokens) in (1, 2) else ''
    noun_points = 5 if noun == expected['noun'].replace('ё', 'е') else 0
    pronoun_points = 5 if pronoun == expected['pronoun'].replace('ё', 'е') else 0
    return {
        'word_id': word_id, 'answer': answer,
        'expected': expected['answer'], 'noun': expected['noun'],
        'noun_points': noun_points, 'pronoun_points': pronoun_points,
        'score': noun_points + pronoun_points,
    }


def run_score(run):
    if run['task_code'] == 'AI_3_10':
        return 100 * sum(a['correct_words'] for a in run['answers']) // NOVGOROD_WORD_COUNT
    return sum(a['score'] for a in run['answers'])


def public_state(run_id, run):
    task_code = run['task_code']
    config = TASKS[task_code]
    completed = len(run['answers']) == config['count']
    current = None if completed else {
        'index': len(run['answers']),
        'audio_path': f"/tasks/lesson3/{config['directory']}/audio/{run['words'][len(run['answers'])]:02d}.wav",
    }
    score = run_score(run)
    return {
        'run_id': run_id, 'task_code': task_code, 'student_code': run['student_code'],
        'word_count': config['count'], 'item_max_score': 100 // config['count'], 'answered': len(run['answers']), 'current': current,
        'answers': run['answers'], 'score': score, 'max_score': 100,
        'total_words': NOVGOROD_WORD_COUNT if task_code == 'AI_3_10' else None,
        'correct_words': sum(a.get('correct_words', 0) for a in run['answers']),
        'passing_score': PASSING_SCORE, 'completed': completed,
        'ok': completed and score >= PASSING_SCORE,
        'saved': run.get('saved', False), 'save_error': run.get('save_error'),
    }
