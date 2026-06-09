import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import element_text, find_child, find_children, parse_question_base, strip_ns


@register_question_parser('numericQuestion')
def parse_numeric(element: ET.Element) -> dict:
    answers_el = find_child(element, 'answers')
    acceptable = []
    if answers_el is not None:
        for child in answers_el:
            tag = strip_ns(child.tag)
            if tag == 'between':
                left = find_child(child, 'leftOperand')
                right = find_child(child, 'rightOperand')
                acceptable.append({
                    'type': 'between',
                    'left_operand': element_text(left) if left is not None else '',
                    'right_operand': element_text(right) if right is not None else '',
                })
            elif tag in ('equal', 'greater', 'greaterOrEqual', 'less', 'lessOrEqual', 'notEqual'):
                acceptable.append({
                    'type': tag,
                    'value': element_text(child),
                })
    return {
        **parse_question_base(element),
        'user_answer': element.get('userAnswer'),
        'acceptable_answers': acceptable,
    }
