import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import find_child, find_children, get_bool_attr, parse_question_base, parse_text_with_equation


@register_question_parser('multipleResponseQuestion')
def parse_multiple_response(element: ET.Element) -> dict:
    answers_el = find_child(element, 'answers')
    answers = []
    if answers_el is not None:
        for answer_el in find_children(answers_el, 'answer'):
            answers.append({
                'text': parse_text_with_equation(answer_el),
                'correct': get_bool_attr(answer_el, 'correct'),
                'selected': get_bool_attr(answer_el, 'selected'),
                'custom_answer': answer_el.get('customAnswer'),
                'score': answer_el.get('score'),
            })
    return {
        **parse_question_base(element),
        'answers': answers,
    }
