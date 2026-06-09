from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Literal, Optional

from . import questions  # noqa: F401 — регистрация парсеров
from .registry import QUESTION_PARSERS
from .types import GroupResult, QuestionBase, QuizReport, QuizSettings, QuizSummary, TextBlock
from .xml_utils import (
    element_text,
    element_to_string,
    find_child,
    find_children,
    get_bool_attr,
    strip_ns,
)

logger = logging.getLogger('courses')

NS = 'http://www.ispringsolutions.com/ispring/quizbuilder/quizresults'


def detect_format(content: str) -> Literal['xml', 'html', 'plain']:
    if not content or not content.strip():
        return 'plain'
    stripped = content.strip()
    if stripped.startswith('<?xml') or stripped.startswith('<quizReport') or 'quizReport' in stripped[:200]:
        return 'xml'
    lower = stripped.lower()
    if '<table' in lower or '<html' in lower or '<body' in lower or '<div' in lower:
        return 'html'
    return 'plain'


def _parse_settings(element: ET.Element) -> QuizSettings:
    passing_score_el = find_child(element, 'passingScore')
    passing_percent_el = find_child(element, 'passingPercent')
    return QuizSettings(
        quiz_type=element.get('quizType', ''),
        max_score=element.get('maxScore'),
        max_normalized_score=element.get('maxNormalizedScore'),
        time_limit=element.get('timeLimit'),
        passing_score=element_text(passing_score_el) if passing_score_el is not None else None,
        passing_percent=element_text(passing_percent_el) if passing_percent_el is not None else None,
    )


def _parse_summary(element: ET.Element) -> QuizSummary:
    variables = []
    variables_el = find_child(element, 'variables')
    if variables_el is not None:
        for var_el in find_children(variables_el, 'variable'):
            variables.append({
                'name': var_el.get('name', ''),
                'title': var_el.get('title', ''),
                'value': var_el.get('value', ''),
            })
    passed = element.get('passed')
    return QuizSummary(
        score=element.get('score'),
        percent=element.get('percent'),
        time=element.get('time'),
        finish_timestamp=element.get('finishTimestamp'),
        passed=passed.lower() == 'true' if passed is not None else None,
        variables=variables,
    )


def parse_summary_from_xml(dr_xml: str) -> dict:
    """Извлекает summary из XML (совместимость с courses.services)."""
    result = {
        'passed': None,
        'score': None,
        'percent': None,
        'finish_timestamp': None,
    }
    if not dr_xml:
        return result
    try:
        report = parse_quiz_report(dr_xml)
        if report is None:
            return result
        result['passed'] = report.summary.passed
        result['score'] = report.summary.score
        result['percent'] = report.summary.percent
        result['finish_timestamp'] = report.summary.finish_timestamp
    except ET.ParseError as e:
        logger.warning('Ошибка парсинга dr XML: %s', e)
    return result


def _parse_groups(element: ET.Element) -> list[GroupResult]:
    return [
        GroupResult(
            name=g.get('name', ''),
            passing_score=g.get('passingScore', ''),
            awarded_score=g.get('awardedScore', ''),
            max_score=g.get('maxScore', ''),
            passing_percent=g.get('passingPercent', ''),
            awarded_percent=g.get('awardedPercent', ''),
            total_questions=g.get('totalQuestions', ''),
            answered_questions=g.get('answeredQuestions', ''),
        )
        for g in find_children(element, 'group')
    ]


def _parse_question(element: ET.Element) -> QuestionBase:
    tag = strip_ns(element.tag)
    parser = QUESTION_PARSERS.get(tag)
    if parser:
        payload = parser(element)
        return QuestionBase(
            type=tag,
            id=payload.get('id', ''),
            status=payload.get('status', ''),
            evaluation_enabled=payload.get('evaluation_enabled', False),
            max_points=payload.get('max_points'),
            max_attempts=payload.get('max_attempts'),
            used_attempts=payload.get('used_attempts'),
            awarded_points=payload.get('awarded_points'),
            direction=payload.get('direction', []),
            feedback=payload.get('feedback', []),
            payload={k: v for k, v in payload.items() if k not in (
                'id', 'status', 'evaluation_enabled', 'max_points', 'max_attempts',
                'used_attempts', 'awarded_points', 'direction', 'feedback',
            )},
        )
    return QuestionBase(
        type='unknown',
        id=element.get('id', ''),
        status=element.get('status', ''),
        evaluation_enabled=get_bool_attr(element, 'evaluationEnabled'),
        raw_xml=element_to_string(element),
        payload={'original_tag': tag},
    )


def parse_quiz_report(xml_content: str) -> Optional[QuizReport]:
    if not xml_content or not xml_content.strip():
        return None
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.warning('Ошибка парсинга quizReport XML: %s', e)
        return None

    if strip_ns(root.tag) != 'quizReport':
        logger.warning('Корневой элемент не quizReport: %s', root.tag)
        return None

    settings_el = find_child(root, 'quizSettings')
    summary_el = find_child(root, 'summary')
    questions_el = find_child(root, 'questions')
    groups_el = find_child(root, 'groups')

    questions_list = []
    if questions_el is not None:
        for child in questions_el:
            questions_list.append(_parse_question(child))

    return QuizReport(
        version=root.get('version', ''),
        settings=_parse_settings(settings_el) if settings_el is not None else QuizSettings(),
        summary=_parse_summary(summary_el) if summary_el is not None else QuizSummary(),
        questions=questions_list,
        groups=_parse_groups(groups_el) if groups_el is not None else [],
    )
