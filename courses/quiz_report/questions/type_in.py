import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import element_text, find_child, find_children, parse_question_base


@register_question_parser('typeInQuestion')
def parse_type_in(element: ET.Element) -> dict:
    acceptable = []
    acceptable_el = find_child(element, 'acceptableAnswers')
    if acceptable_el is not None:
        acceptable = [element_text(a) for a in find_children(acceptable_el, 'answer')]
    return {
        **parse_question_base(element),
        'user_answer': element.get('userAnswer', ''),
        'acceptable_answers': acceptable,
    }
