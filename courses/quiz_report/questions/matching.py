import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import (
    find_child,
    find_children,
    get_int_attr,
    parse_question_base,
    parse_text_with_equation,
)


def _parse_matches(element: ET.Element | None) -> list[dict]:
    if element is None:
        return []
    return [
        {
            'premise_index': get_int_attr(m, 'premiseIndex'),
            'response_index': get_int_attr(m, 'responseIndex'),
        }
        for m in find_children(element, 'match')
    ]


@register_question_parser('matchingQuestion')
def parse_matching(element: ET.Element) -> dict:
    premises_el = find_child(element, 'premises')
    responses_el = find_child(element, 'responses')
    premises = [parse_text_with_equation(p) for p in find_children(premises_el, 'premise')] if premises_el else []
    responses = [parse_text_with_equation(r) for r in find_children(responses_el, 'response')] if responses_el else []
    correct_matches = _parse_matches(find_child(element, 'matches'))
    user_matches = _parse_matches(find_child(element, 'userAnswer'))

    def _response_at(index: int | None):
        if index is None or index < 0 or index >= len(responses):
            return []
        return responses[index]

    rows = []
    for i, premise in enumerate(premises):
        user_resp = []
        correct_resp = []
        for m in user_matches:
            if m['premise_index'] == i:
                user_resp = _response_at(m['response_index'])
                break
        for m in correct_matches:
            if m['premise_index'] == i:
                correct_resp = _response_at(m['response_index'])
                break
        rows.append({
            'premise': premise,
            'user_response': user_resp,
            'correct_response': correct_resp,
        })

    return {
        **parse_question_base(element),
        'premises': premises,
        'responses': responses,
        'matches': correct_matches,
        'user_answer': user_matches,
        'rows': rows,
    }
