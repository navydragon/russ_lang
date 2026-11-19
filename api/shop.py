"""Shared source and accusative answer key for «В магазине»."""
import json
from pathlib import Path
import re


SOURCE = json.loads(
    (Path(__file__).resolve().parents[1] / 'tasks/lesson6/shop/source.json').read_text(encoding='utf-8')
)
REFERENCE_TEXT = '\n'.join(SOURCE['paragraphs'])
WORDS = re.findall(r'[А-Яа-яЁё]+', REFERENCE_TEXT)
ACCUSATIVE_INDEXES = frozenset({
    8, 18,  # продукты, рубль (пакет стоит 51 рубль)
    52, 53, 54,  # в гости, друзей, что делать
    85, 91, 93, 96,  # килограмм, пачку, банку, десяток
    104, 105, 112, 119, 120,  # вкусный ужин, меня, интересные истории
    128, 132,  # сто рублей, сто друзей — each noun is genitive after «сто»
})
