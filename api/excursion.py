"""Shared source and exact targets for the three Moscow excursion tasks."""
import json
import re
from pathlib import Path


SOURCE = json.loads((Path(__file__).resolve().parent.parent / 'tasks' / 'lesson7' / 'excursion_text.json').read_text(encoding='utf-8'))
REFERENCE_TEXT = '\n\n'.join(SOURCE['paragraphs'])
WORD_RE = re.compile(r'[А-Яа-яЁёA-Za-z0-9]+')
GENITIVE_PLURAL_FORMS = frozenset({
    'самых', 'больших', 'городов', 'квадратных', 'километров', 'миллионов',
    'человек', 'университетов', 'школ', 'тысяч', 'студентов', 'школьников',
    'наук', 'факультетов', 'профессоров', 'преподавателей', 'книг',
    'бассейнов', 'театров', 'музеев', 'выставок', 'кинотеатров',
    'концертных', 'залов', 'библиотек', 'станций', 'линий', 'поездов',
    'пассажиров', 'часов', 'минут', 'секунд', 'градусов',
})
TIME_PHRASES = (
    'в 1935 году', 'сегодня', 'каждый день', 'в 5 часов 30 минут утра',
    'в час ночи', 'через 90 секунд', '2 3 минуты', '240 часов в год',
    'летом', 'зимой',
)


def words_and_targets():
    words = WORD_RE.findall(REFERENCE_TEXT)
    lowered = [word.casefold().replace('ё', 'е') for word in words]
    grammar = {index for index, word in enumerate(lowered) if word in GENITIVE_PLURAL_FORMS}
    time = set()
    for phrase in TIME_PHRASES:
        tokens = [word.casefold().replace('ё', 'е') for word in WORD_RE.findall(phrase)]
        for start in range(len(words) - len(tokens) + 1):
            if lowered[start:start + len(tokens)] == tokens:
                time.update(range(start, start + len(tokens)))
    return words, {'genitive_plural': grammar, 'time': time}


def score_selection(selected):
    words, targets = words_and_targets()
    if not isinstance(selected, dict) or set(selected) != set(targets):
        raise ValueError('Выберите слова в обеих категориях.')
    score_parts = {}
    for category, expected in targets.items():
        values = selected[category]
        if not isinstance(values, list) or any(type(value) is not int or value < 0 or value >= len(words) for value in values):
            raise ValueError('Некорректные номера слов.')
        chosen = set(values)
        correct = len(chosen & expected)
        extra = len(chosen - expected)
        points = round(50 * max(0, correct - extra) / len(expected))
        score_parts[category] = {'points': points, 'correct': correct, 'total': len(expected), 'extra': extra,
                                 'missed': sorted(expected - chosen), 'false': sorted(chosen - expected)}
    score = sum(part['points'] for part in score_parts.values())
    return {'ok': score >= 60, 'score': score, 'passing_score': 60, 'max_score': 100,
            'categories': score_parts}
