"""Shared source and genitive answer key for «Московский Кремль»."""
import json
from pathlib import Path
import re


SOURCE = json.loads(
    (Path(__file__).resolve().parents[1] / 'tasks/lesson6/kremlin/source.json').read_text(encoding='utf-8')
)
_TEXT = '\n'.join(SOURCE['paragraphs'])
# Keep just the numeric notation so that graders do not expect a date twice.
READING_REFERENCE_TEXT = re.sub(r'(?<=\d) \([^()]+\)(?= году)', '', _TEXT)
WORDS = re.findall(r'[А-Яа-яЁё]+', _TEXT)
GENITIVE_INDEXES = frozenset({
    1, 7, 9,  # людей, Кремля, Москвы
    55, 56, 59,  # метров, сантиметров, сантиметра
    61, 62, 63, 64, 66, 67, 68,  # часовой стрелки, метра, сантиметров, минутной, метра, сантиметров
})
