from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


TextBlockType = Literal['text', 'equation', 'picture']


@dataclass
class TextBlock:
    type: TextBlockType
    value: str = ''
    alt_text: str = ''


@dataclass
class QuizSettings:
    quiz_type: str = ''
    max_score: Optional[str] = None
    max_normalized_score: Optional[str] = None
    time_limit: Optional[str] = None
    passing_percent: Optional[str] = None
    passing_score: Optional[str] = None


@dataclass
class QuizSummary:
    score: Optional[str] = None
    percent: Optional[str] = None
    time: Optional[str] = None
    finish_timestamp: Optional[str] = None
    passed: Optional[bool] = None
    variables: list[dict[str, str]] = field(default_factory=list)


@dataclass
class GroupResult:
    name: str = ''
    passing_score: str = ''
    awarded_score: str = ''
    max_score: str = ''
    passing_percent: str = ''
    awarded_percent: str = ''
    total_questions: str = ''
    answered_questions: str = ''


@dataclass
class QuestionBase:
    type: str
    id: str = ''
    status: str = ''
    evaluation_enabled: bool = False
    max_points: Optional[str] = None
    max_attempts: Optional[str] = None
    used_attempts: Optional[str] = None
    awarded_points: Optional[str] = None
    direction: list[TextBlock] = field(default_factory=list)
    feedback: list[TextBlock] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    raw_xml: str = ''


@dataclass
class QuizReport:
    version: str = ''
    settings: QuizSettings = field(default_factory=QuizSettings)
    summary: QuizSummary = field(default_factory=QuizSummary)
    questions: list[QuestionBase] = field(default_factory=list)
    groups: list[GroupResult] = field(default_factory=list)
