import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import find_child, find_children, get_bool_attr, get_float_attr, parse_question_base, strip_ns


def _parse_hotspot(el: ET.Element) -> dict:
    return {
        'type': strip_ns(el.tag),
        'x': get_float_attr(el, 'x'),
        'y': get_float_attr(el, 'y'),
        'width': get_float_attr(el, 'width'),
        'height': get_float_attr(el, 'height'),
        'marked': get_bool_attr(el, 'marked'),
        'label': el.get('label', ''),
        'correct': get_bool_attr(el, 'correct') if el.get('correct') is not None else None,
        'points': el.get('points'),
    }


@register_question_parser('hotspotQuestion')
def parse_hotspot(element: ET.Element) -> dict:
    user_answer_el = find_child(element, 'userAnswer')
    points = []
    if user_answer_el is not None:
        for point_el in find_children(user_answer_el, 'point'):
            points.append({
                'x': get_float_attr(point_el, 'x'),
                'y': get_float_attr(point_el, 'y'),
            })
    hotspots_el = find_child(element, 'hotspots')
    hotspots = []
    if hotspots_el is not None:
        for child in hotspots_el:
            if strip_ns(child.tag) in ('rectangle', 'oval', 'freeform'):
                hotspots.append(_parse_hotspot(child))
    return {
        **parse_question_base(element),
        'user_points': points,
        'hotspots': hotspots,
    }
