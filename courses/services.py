from students.models import Student
from courses.models import Task, TaskAttempt, StudentTask
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from typing import Optional
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


def save_quiz_result(parsed_data: dict, html_body: Optional[str] = None) -> bool:
    """
    Сохраняет результат выполнения задания в базу данных.
    
    Args:
        parsed_data: Словарь с распарсенными данными из письма:
            - user_id: код студента
            - task_code: код задания
            - date: дата выполнения
            - score: строка с результатом
            - result: True если пройдено, False если не пройдено
        html_body: HTML тело письма для сохранения в поле results
            
    Returns:
        True при успешном сохранении, False при ошибке
    """
    try:
        # 1. Проверяем наличие обязательных данных
        user_id = parsed_data.get('user_id')
        task_code = parsed_data.get('task_code')
        
        if not user_id or not task_code:
            logger.warning(f"Недостаточно данных для сохранения: user_id={user_id}, task_code={task_code}")
            return False
        
        # 2. Находим студента по коду
        try:
            student = Student.objects.get(code=user_id)
        except Student.DoesNotExist:
            logger.error(f"Студент с кодом {user_id} не найден")
            return False
        except Exception as e:
            logger.error(f"Ошибка поиска студента с кодом {user_id}: {e}")
            return False
        
        # 3. Находим задание по коду (точное совпадение)
        try:
            task = Task.objects.get(code=task_code)
        except Task.DoesNotExist:
            logger.error(f"Задание с кодом {task_code} не найдено")
            return False
        except Exception as e:
            logger.error(f"Ошибка поиска задания с кодом {task_code}: {e}")
            return False
        
        # 4. Парсим дату
        date_str = parsed_data.get('date')
        attempt_datetime = parse_russian_date(date_str) if date_str else None
        
        if not attempt_datetime:
            logger.warning(f"Не удалось распарсить дату: {date_str}, используем текущее время")
            attempt_datetime = timezone.now()
        
        # 5. Извлекаем данные из score
        score_str = parsed_data.get('score')
        score_value = extract_score_value(score_str) if score_str else None
        score_percent = extract_score_percent(score_str) if score_str else None
        
        # 6. Определяем статус выполнения
        is_completed = parsed_data.get('result', False)
        
        # 7. Создаем TaskAttempt
        # Сохраняем HTML тело письма в поле results
        results_content = html_body if html_body else ""
        
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
        
        # 8. Если задание пройдено, создаем StudentTask
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
