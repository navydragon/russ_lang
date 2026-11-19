"""Задания из авторских документов, ожидающие реализации и материалов."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PlannedAssignment:
    lesson: int
    source_number: str
    name: str
    student_action: str
    missing: str
    code: str = ''


PLANNED_ASSIGNMENTS: tuple[PlannedAssignment, ...] = ()
