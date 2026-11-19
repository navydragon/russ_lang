"""Scoring for tasks that ask learners to select word occurrences."""


def score_selected_words(selected, words, expected):
    if not isinstance(selected, list) or any(type(index) is not int or not 0 <= index < len(words) for index in selected):
        raise ValueError('Некорректные номера слов.')
    chosen = set(selected)
    correct = len(chosen & expected)
    extra = len(chosen - expected)
    total = len(expected)
    score = round(100 * max(0, correct - extra) / total)
    return {'ok': score >= 60, 'score': score, 'correct': correct, 'extra': extra, 'total': total}
