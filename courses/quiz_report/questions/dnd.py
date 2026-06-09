import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import element_text, find_child, find_children, get_int_attr, parse_question_base


def _parse_objects(parent: ET.Element | None, tag: str) -> list[dict]:
    if parent is None:
        return []
    return [
        {'id': obj.get('id', ''), 'text': element_text(obj)}
        for obj in find_children(parent, tag)
    ]


def _parse_placements(element: ET.Element | None) -> list[dict]:
    if element is None:
        return []
    return [
        {
            'object_index': get_int_attr(m, 'objectIndex'),
            'destination_index': get_int_attr(m, 'destinationIndex'),
            'text': element_text(m),
        }
        for m in find_children(element, 'match')
    ]


@register_question_parser('dndQuestion')
def parse_dnd(element: ET.Element) -> dict:
    objects = _parse_objects(find_child(element, 'objects'), 'object')
    destinations = _parse_objects(find_child(element, 'destinations'), 'destination')
    correct = _parse_placements(find_child(element, 'matches'))
    user = _parse_placements(find_child(element, 'userAnswer'))

    def _dest_text(index: int | None) -> str:
        if index is None or index < 0 or index >= len(destinations):
            return '—'
        return destinations[index].get('text', '—')

    rows = []
    for i, obj in enumerate(objects):
        user_dest = '—'
        correct_dest = '—'
        for p in user:
            if p['object_index'] == i:
                user_dest = _dest_text(p['destination_index'])
                break
        for p in correct:
            if p['object_index'] == i:
                correct_dest = _dest_text(p['destination_index'])
                break
        rows.append({
            'object_text': obj.get('text', ''),
            'user_destination': user_dest,
            'correct_destination': correct_dest,
        })

    return {
        **parse_question_base(element),
        'objects': objects,
        'destinations': destinations,
        'matches': correct,
        'user_answer': user,
        'rows': rows,
    }
