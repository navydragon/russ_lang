from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Callable

QUESTION_PARSERS: dict[str, Callable[[ET.Element], dict]] = {}


def register_question_parser(tag: str):
    def decorator(fn: Callable[[ET.Element], dict]):
        QUESTION_PARSERS[tag] = fn
        return fn
    return decorator
