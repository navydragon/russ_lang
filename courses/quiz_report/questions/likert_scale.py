import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import (
    element_text,
    find_child,
    find_children,
    get_bool_attr,
    get_int_attr,
    parse_question_base,
    parse_text_with_equation,
)


@register_question_parser('likertScaleQuestion')
def parse_likert_scale(element: ET.Element) -> dict:
    statements_el = find_child(element, 'statements')
    labels_el = find_child(element, 'scaleLabels')
    user_answer_el = find_child(element, 'userAnswer')

    statements = [parse_text_with_equation(s) for s in find_children(statements_el, 'statement')] if statements_el else []
    labels = [element_text(l) for l in find_children(labels_el, 'label')] if labels_el else []
    matches = []
    if user_answer_el is not None:
        for match_el in find_children(user_answer_el, 'match'):
            matches.append({
                'statement_index': get_int_attr(match_el, 'statementIndex'),
                'label_index': get_int_attr(match_el, 'labelIndex'),
            })
    return {
        **parse_question_base(element),
        'statements': statements,
        'labels': labels,
        'number_from_zero': get_bool_attr(labels_el, 'numberFromZero') if labels_el else False,
        'user_matches': matches,
    }
