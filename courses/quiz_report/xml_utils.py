from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Optional

from .types import TextBlock


def strip_ns(tag: str) -> str:
    if '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def find_child(parent: ET.Element, name: str) -> Optional[ET.Element]:
    for child in parent:
        if strip_ns(child.tag) == name:
            return child
    return None


def find_children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in parent if strip_ns(child.tag) == name]


def get_attr(element: ET.Element, name: str, default: Optional[str] = None) -> Optional[str]:
    return element.get(name, default)


def get_bool_attr(element: ET.Element, name: str, default: bool = False) -> bool:
    value = element.get(name)
    if value is None:
        return default
    return value.lower() == 'true'


def get_int_attr(element: ET.Element, name: str) -> Optional[int]:
    value = element.get(name)
    if value is None or value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None


def get_float_attr(element: ET.Element, name: str) -> Optional[float]:
    value = element.get(name)
    if value is None or value == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def element_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ''
    return ''.join(element.itertext()).strip()


def parse_text_with_equation(element: Optional[ET.Element]) -> list[TextBlock]:
    if element is None:
        return []

    blocks: list[TextBlock] = []
    if element.text:
        text = element.text.strip()
        if text:
            blocks.append(TextBlock(type='text', value=text))

    for child in element:
        tag = strip_ns(child.tag)
        if tag == 'text':
            value = element_text(child)
            if value:
                blocks.append(TextBlock(type='text', value=value))
        elif tag == 'equation':
            latex_el = find_child(child, 'latex')
            latex = element_text(latex_el) if latex_el is not None else element_text(child)
            blocks.append(TextBlock(type='equation', value=latex))
        elif tag == 'picture':
            blocks.append(TextBlock(
                type='picture',
                value='',
                alt_text=child.get('altText', ''),
            ))

        if child.tail:
            tail = child.tail.strip()
            if tail:
                blocks.append(TextBlock(type='text', value=tail))

    return blocks


def parse_question_base(element: ET.Element) -> dict[str, Any]:
    direction_el = find_child(element, 'direction')
    feedback_el = find_child(element, 'feedback')
    return {
        'id': element.get('id', ''),
        'status': element.get('status', ''),
        'evaluation_enabled': get_bool_attr(element, 'evaluationEnabled'),
        'max_points': element.get('maxPoints'),
        'max_attempts': element.get('maxAttempts'),
        'used_attempts': element.get('usedAttempts'),
        'awarded_points': element.get('awardedPoints'),
        'direction': parse_text_with_equation(direction_el),
        'feedback': parse_text_with_equation(feedback_el),
    }


def parse_answers_list(parent: ET.Element, child_tag: str = 'answer') -> list[list[TextBlock]]:
    answers_el = find_child(parent, 'answers')
    if answers_el is None:
        return []
    return [parse_text_with_equation(child) for child in find_children(answers_el, child_tag)]


def element_to_string(element: ET.Element) -> str:
    return ET.tostring(element, encoding='unicode')
