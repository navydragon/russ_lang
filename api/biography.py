"""Shared source and genitive answer key for «Моя биография»."""
import json
from pathlib import Path
import re


SOURCE = json.loads(
    (Path(__file__).resolve().parents[1] / 'tasks/lesson6/biography/source.json').read_text(encoding='utf-8')
)
REFERENCE_TEXT = '\n'.join(SOURCE['paragraphs'])
WORDS = re.findall(r'[А-Яа-яЁё]+', REFERENCE_TEXT)
GENITIVE_INDEXES = frozenset({
    3, 4, 6, 7,  # Восточной Сибири, небольшого города
    12, 13, 14,  # глубокого красивого озера («Байкал» — название в начальной форме)
    30, 31, 32, 33, 34,  # первого курса Университета инженеров транспорта
    40, 41, 42,  # своего родного города
})
