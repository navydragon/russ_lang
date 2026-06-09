from students.models import Student
from courses.models import Task, TaskAttempt, StudentTask
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
import re
import logging
logger = logging.getLogger('courses')


def parse_russian_date(date_str: str) -> Optional[datetime]:
    """
    Парсит дату из русского формата в datetime объект.
    
    Примеры форматов:
    - "22 декабря 2025 г. 13:04"
    - "1 января 2024 г. 09:30"
    
    Args:
        date_str: Строка с датой в русском формате
        
    Returns:
        datetime объект или None при ошибке парсинга
    """
    if not date_str:
        return None
    
    # Словарь русских названий месяцев
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    
    try:
        # Паттерн для парсинга: "22 декабря 2025 г. 13:04"
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+г\.\s+(\d{1,2}):(\d{2})'
        match = re.search(pattern, date_str)
        
        if not match:
            logger.warning(f"Не удалось распарсить дату: {date_str}")
            return None
        
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        
        if month_name not in months:
            logger.warning(f"Неизвестный месяц: {month_name}")
            return None
        
        month = months[month_name]
        
        return datetime(year, month, day, hour, minute)
        
    except Exception as e:
        logger.error(f"Ошибка парсинга даты '{date_str}': {e}")
        return None


def extract_score_percent(score_str: str) -> Optional[Decimal]:
    """
    Извлекает процент из строки score.
    
    Примеры:
    - "10 / 10 (100%)" -> 100.00
    - "5 / 10 (50%)" -> 50.00
    
    Args:
        score_str: Строка с результатом, например "10 / 10 (100%)"
        
    Returns:
        Decimal значение процента или None при ошибке
    """
    if not score_str:
        return None
    
    try:
        # Ищем паттерн (число%)
        pattern = r'\((\d+)%\)'
        match = re.search(pattern, score_str)
        
        if match:
            percent = int(match.group(1))
            return Decimal(percent)
        
        logger.warning(f"Не удалось извлечь процент из: {score_str}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка извлечения процента из '{score_str}': {e}")
        return None


def extract_score_value(score_str: str) -> Optional[Decimal]:
    """
    Извлекает числовое значение баллов из строки score.
    
    Примеры:
    - "10 / 10 (100%)" -> 10.00
    - "5 / 10 (50%)" -> 5.00
    
    Args:
        score_str: Строка с результатом, например "10 / 10 (100%)"
        
    Returns:
        Decimal значение баллов или None при ошибке
    """
    if not score_str:
        return None
    
    try:
        # Ищем первое число (полученные баллы)
        pattern = r'^(\d+)'
        match = re.search(pattern, score_str)
        
        if match:
            score = int(match.group(1))
            return Decimal(score)
        
        logger.warning(f"Не удалось извлечь баллы из: {score_str}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка извлечения баллов из '{score_str}': {e}")
        return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def parse_dr_summary(dr_xml: str) -> dict:
    """
    Извлекает summary из XML детальных результатов iSpring (поле dr).
    """
    from courses.quiz_report import parse_summary_from_xml
    return parse_summary_from_xml(dr_xml)


def parse_ispring_post(post) -> dict:
    """
    Преобразует POST-данные iSpring QuizMaker в формат для save_quiz_result.
    """
    dr_xml = post.get('dr', '')
    summary = parse_dr_summary(dr_xml)

    score_value = _to_decimal(post.get('tp')) or _to_decimal(post.get('sp'))
    if score_value is None:
        score_value = _to_decimal(summary.get('score'))

    score_percent = _to_decimal(summary.get('percent'))

    passed = summary.get('passed')
    if passed is None:
        tp = _to_decimal(post.get('tp'))
        ps = _to_decimal(post.get('ps'))
        if tp is not None and ps is not None:
            passed = tp >= ps
        else:
            passed = False

    return {
        'sid': post.get('sid') or None,
        'task_code': post.get('qt') or None,
        'date': summary.get('finish_timestamp'),
        'score_value': score_value,
        'score_percent': score_percent,
        'result': passed,
        'results_content': dr_xml,
    }


def _find_student(parsed_data: dict) -> Optional[Student]:
    # sid из iSpring API и user_id из email-forwarder — это код студента (Student.code)
    student_code = parsed_data.get('sid') or parsed_data.get('user_id')
    if student_code:
        return Student.objects.filter(code=student_code).first()
    return None


def save_quiz_result(parsed_data: dict, html_body: Optional[str] = None) -> bool:
    """
    Сохраняет результат выполнения задания в базу данных.

    Args:
        parsed_data: Словарь с распарсенными данными:
            - sid: код студента из iSpring API (Student.code)
            - user_id: код студента из email-forwarder (Student.code)
            - task_code: код задания
            - date: дата выполнения (строка или datetime)
            - score: строка с результатом (email)
            - score_value, score_percent: числовые значения (API)
            - result: True если пройдено, False если не пройдено
            - results_content: подробный результат (XML dr или HTML)
        html_body: HTML тело письма для сохранения в поле results

    Returns:
        True при успешном сохранении, False при ошибке
    """
    try:
        student_code = parsed_data.get('sid') or parsed_data.get('user_id')
        task_code = parsed_data.get('task_code')

        if not task_code or not student_code:
            logger.warning(
                f"Недостаточно данных для сохранения: "
                f"student_code={student_code}, task_code={task_code}"
            )
            return False

        student = _find_student(parsed_data)
        if not student:
            logger.error(f"Студент не найден по коду: {student_code}")
            return False

        # Находим задание по коду (точное совпадение)
        try:
            task = Task.objects.get(code=task_code)
        except Task.DoesNotExist:
            logger.error(f"Задание с кодом {task_code} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка поиска задания с кодом {task_code}: {e}")
            return False
        
        date_value = parsed_data.get('date')
        if isinstance(date_value, datetime):
            attempt_datetime = date_value
        elif date_value:
            attempt_datetime = parse_russian_date(str(date_value))
        else:
            attempt_datetime = None

        if not attempt_datetime:
            logger.warning(
                f"Не удалось распарсить дату: {date_value}, используем текущее время"
            )
            attempt_datetime = timezone.now()
        elif timezone.is_naive(attempt_datetime):
            attempt_datetime = timezone.make_aware(attempt_datetime)

        score_value = parsed_data.get('score_value')
        score_percent = parsed_data.get('score_percent')
        if score_value is None or score_percent is None:
            score_str = parsed_data.get('score')
            if score_value is None and score_str:
                score_value = extract_score_value(score_str)
            if score_percent is None and score_str:
                score_percent = extract_score_percent(score_str)

        is_completed = parsed_data.get('result', False)

        results_content = parsed_data.get('results_content') or html_body or ''
        
        task_attempt = TaskAttempt.objects.create(
            student=student,
            task=task,
            datetime=attempt_datetime,
            is_completed=is_completed,
            score=score_value,
            score_percent=score_percent,
            results=results_content
        )
        
        logger.info(f"Создана попытка выполнения задания: {task_attempt}")
        
        # Если задание пройдено, создаем StudentTask
        if is_completed:
            # Подсчитываем количество существующих попыток (все попытки)
            attempts_count = TaskAttempt.objects.filter(
                student=student,
                task=task
            ).count()
            
            # Номер попытки = количество попыток (включая только что созданную)
            completion_attempt = attempts_count
            
            # Проверяем, существует ли уже StudentTask
            student_task_exists = StudentTask.objects.filter(
                student=student,
                task=task
            ).exists()
            
            if not student_task_exists:
                # Создаем StudentTask
                completion_date = attempt_datetime.date()
                
                student_task = StudentTask.objects.create(
                    student=student,
                    task=task,
                    completion_date=completion_date,
                    completion_attempt=completion_attempt
                )
                
                logger.info(f"Создано завершенное задание студента: {student_task}")
            else:
                logger.info(f"StudentTask для студента {student} и задания {task} уже существует, пропускаем создание")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сохранения результата задания: {e}", exc_info=True)
        return False
