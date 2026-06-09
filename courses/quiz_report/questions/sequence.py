import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import find_child, find_children, get_int_attr, parse_question_base, parse_text_with_equation


@register_question_parser('sequenceQuestion')
def parse_sequence(element: ET.Element) -> dict:
    answers_el = find_child(element, 'answers')
    answers = []
    if answers_el is not None:
        for answer_el in find_children(answers_el, 'answer'):
            answers.append({
                'text': parse_text_with_equation(answer_el),
                'original_index': get_int_attr(answer_el, 'originalIndex'),
            })
    return {
        **parse_question_base(element),
        'answers': answers,
    }
