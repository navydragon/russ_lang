import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import (
    element_text,
    find_child,
    find_children,
    get_int_attr,
    parse_question_base,
    parse_text_with_equation,
    strip_ns,
)


@register_question_parser('multipleChoiceTextQuestion')
def parse_multiple_choice_text(element: ET.Element) -> dict:
    details_el = find_child(element, 'details')
    parts = []
    if details_el is not None:
        for child in details_el:
            tag = strip_ns(child.tag)
            if tag == 'text':
                parts.append({'type': 'text', 'value': element_text(child)})
            elif tag == 'equation':
                parts.append({'type': 'equation', 'value': element_text(find_child(child, 'latex') or child)})
            elif tag == 'blank':
                acceptable = [element_text(a) for a in find_children(child, 'answer')]
                user_idx = get_int_attr(child, 'userAnswerIndex')
                correct_idx = get_int_attr(child, 'correctAnswerIndex')
                user_text = acceptable[user_idx] if user_idx is not None and 0 <= user_idx < len(acceptable) else '—'
                parts.append({
                    'type': 'blank',
                    'user_answer_index': user_idx,
                    'correct_answer_index': correct_idx,
                    'acceptable_answers': acceptable,
                    'user_answer_text': user_text,
                    'is_correct': user_idx is not None and user_idx == correct_idx,
                })
    return {
        **parse_question_base(element),
        'details': parts,
    }
