import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import element_text, find_child, parse_question_base


@register_question_parser('essayQuestion')
def parse_essay(element: ET.Element) -> dict:
    user_answer_el = find_child(element, 'userAnswer')
    user_answer = element_text(user_answer_el) if user_answer_el is not None else ''
    return {
        **parse_question_base(element),
        'user_answer': user_answer,
    }
