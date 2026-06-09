import xml.etree.ElementTree as ET

from ..registry import register_question_parser
from ..xml_utils import (
    element_text,
    find_child,
    find_children,
    get_bool_attr,
    parse_question_base,
    strip_ns,
)


@register_question_parser('wordBankQuestion')
def parse_word_bank(element: ET.Element) -> dict:
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
                parts.append({
                    'type': 'blank',
                    'user_answer': child.get('userAnswer', ''),
                    'correct': get_bool_attr(child, 'correct'),
                })
    words_el = find_child(element, 'words')
    extra_words = [element_text(w) for w in find_children(words_el, 'word')] if words_el else []
    return {
        **parse_question_base(element),
        'details': parts,
        'extra_words': extra_words,
    }
