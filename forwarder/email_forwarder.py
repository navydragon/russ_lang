import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import time
import logging
from typing import Optional, List
import os
import re
from email.header import decode_header
from html.parser import HTMLParser
from courses.services import save_quiz_result
from students.models import Student
from users.models import User

# Используем Django logging
logger = logging.getLogger('forwarder')


class EmailForwarder:
    def __init__(
        self,
        imap_server: str,
        imap_port: int,
        smtp_server: str,
        smtp_port: int,
        email_address: str,
        email_password: str,
        forward_to: str,
        use_tls: bool = True
    ):
        """
        Инициализация пересылки писем
        
        Args:
            imap_server: Адрес IMAP сервера (например, 'imap.gmail.com')
            imap_port: Порт IMAP (обычно 993 для SSL)
            smtp_server: Адрес SMTP сервера (например, 'smtp.gmail.com')
            smtp_port: Порт SMTP (обычно 587 для TLS или 465 для SSL)
            email_address: Ваш email адрес
            email_password: Пароль или App Password для Gmail
            forward_to: Адрес для пересылки писем
            use_tls: Использовать TLS (True для порта 587) или SSL (False для порта 465)
        """
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
        self.forward_to = forward_to
        self.use_tls = use_tls
        self.processed_uids = set()
        
    def decode_mime_words(self, s: str) -> str:
        """Декодирует MIME заголовки"""
        if not s:
            return ""
        decoded = decode_header(s)
        return ''.join(
            text.decode(encoding or 'utf-8', errors='ignore') if isinstance(text, bytes) else text
            for text, encoding in decoded
        )
    
    def parse_user_id(self, text_body: Optional[str], html_body: Optional[str]) -> Optional[str]:
        """
        Парсит User ID из текста письма
        
        Args:
            text_body: Текстовая версия письма
            html_body: HTML версия письма
            
        Returns:
            User ID в виде строки или None, если не найден
        """
        # Сначала пробуем найти в текстовой версии
        if text_body:
            # Паттерны для поиска ID пользователя (английские и русские варианты)
            patterns = [
                r'ID\s+пользователя\s*[:\t]\s*(\d+)',  # ID пользователя: 321
                r'User\s+ID\s*[:\t]\s*(\d+)',  # User ID: 321
                r'UserID\s*[:\t]\s*(\d+)',  # UserID: 321
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_body, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        # Если не нашли в тексте, пробуем в HTML
        if html_body:
            # Пробуем найти в HTML как есть
            patterns = [
                r'ID\s+пользователя\s*[:\t]\s*(\d+)',  # ID пользователя: 321
                r'<td[^>]*>ID\s+пользователя[^<]*</td>\s*<td[^>]*>(\d+)</td>',  # В таблице HTML
                r'User\s+ID\s*[:\t]\s*(\d+)',  # User ID: 321
                r'UserID\s*[:\t]\s*(\d+)',  # UserID: 321
                r'<td[^>]*>User\s+ID[^<]*</td>\s*<td[^>]*>(\d+)</td>',  # В таблице HTML
                r'User\s+ID[^:]*:\s*(\d+)',  # User ID: 321 (с вариациями)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_body, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Пробуем извлечь текст из HTML и искать там
            try:
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = ""
                    def handle_data(self, data):
                        self.text += data + " "
                
                parser = TextExtractor()
                parser.feed(html_body)
                clean_text = parser.text
                
                # Используем простые паттерны для извлеченного текста
                simple_patterns = [
                    r'ID\s+пользователя\s*[:\t]\s*(\d+)',  # ID пользователя: 321
                    r'User\s+ID\s*[:\t]\s*(\d+)',  # User ID: 321
                    r'UserID\s*[:\t]\s*(\d+)',  # UserID: 321
                ]
                
                for pattern in simple_patterns:
                    match = re.search(pattern, clean_text, re.IGNORECASE)
                    if match:
                        return match.group(1)
            except Exception as e:
                logger.debug(f"Ошибка при извлечении текста из HTML: {e}")
        
        return None
    
    def parse_email_html(self, html_body: Optional[str], subject: Optional[str] = None) -> dict:
        """
        Парсит HTML письма и извлекает структурированные данные
        
        Args:
            html_body: HTML версия письма
            subject: Тема письма для определения результата (Passed/Failed)
            
        Returns:
            Словарь с ключами: user_id, task_code, date, score, result
            Значения могут быть строками или None, если не найдены
            result: True если [Passed], False если [Failed], None если не определено
        """
        result = {
            'user_id': None,
            'task_code': None,
            'date': None,
            'score': None,
            'result': None
        }
        
        if not html_body:
            return result
        
        # 1. Извлекаем user_id - используем существующую логику
        user_id = self.parse_user_id(None, html_body)
        if user_id:
            # Проверяем, существует ли студент с таким кодом в базе данных
            student = self.find_student_by_code(user_id)
            if student:
                # Используем извлеченный ID (student.code == user_id, так как искали по code=user_id)
                result['user_id'] = user_id
            else:
                # Если студент не найден, используем извлеченный ID напрямую
                # save_quiz_result() также проверит наличие студента и вернет False, если не найден
                result['user_id'] = user_id
                logger.warning(f"Студент с кодом {user_id} не найден, используем извлеченный ID")
        
        # 2. Извлекаем task_code - ищем паттерн task[\d.]+ или task[\w.]+
        # Сначала пробуем найти в теме письма (формат: [task1.2.1_...])
        if subject:
            task_patterns_subject = [
                r'\[task[\d.]+[^\]]*\]',  # [task1.2.1_Разместите существительные]
                r'task[\d.]+',  # task1.2.1
            ]
            for pattern in task_patterns_subject:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    # Извлекаем только task код без скобок и дополнительного текста
                    task_match = re.search(r'task[\d.]+', match.group(0), re.IGNORECASE)
                    if task_match:
                        result['task_code'] = task_match.group(0)
                        logger.info(f"task_code найден в теме письма: {result['task_code']}")
                        break
        
        # Если не нашли в теме, ищем в HTML теле письма
        if not result['task_code']:
            task_patterns = [
                r'task[\d.]+',  # task1.1, task2.3.4
                r'task[\w.]+',  # task1.1_Задание, task_1.1
            ]
            for pattern in task_patterns:
                match = re.search(pattern, html_body, re.IGNORECASE)
                if match:
                    result['task_code'] = match.group(0)
                    logger.info(f"task_code найден в HTML теле: {result['task_code']}")
                    break
        
        if not result['task_code']:
            logger.warning("task_code не найден ни в теме письма, ни в HTML теле")
        
        # 3. Извлекаем date - ищем в структуре <td>...<td><b>дата с годом и временем</b></td>
        # Паттерн: ищем <td> с <b> внутри, содержащий год (4 цифры) и время (часы:минуты)
        date_patterns = [
            r'<td[^>]*><b>([^<]*\d{4}[^<]*\d{1,2}:\d{2}[^<]*)</b></td>',  # Дата в <b> внутри <td>
            r'<td[^>]*><strong>([^<]*\d{4}[^<]*\d{1,2}:\d{2}[^<]*)</strong></td>',  # Дата в <strong> внутри <td>
            r'<b>([^<]*\d{4}[^<]*\d{1,2}:\d{2}[^<]*)</b>',  # Просто <b> с датой
        ]
        for pattern in date_patterns:
            match = re.search(pattern, html_body, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                # Очищаем от HTML entities
                date_str = date_str.replace('&nbsp;', ' ').replace('&amp;', '&')
                result['date'] = date_str
                break
        
        # 4. Извлекаем score - ищем паттерн "число / число (число%)"
        score_patterns = [
            r'(\d+\s*/\s*\d+\s*\(\d+%\))',  # 10 / 10 (100%)
            r'(\d+\s*/\s*\d+\s*\(\s*\d+%\s*\))',  # С пробелами
            r'<td[^>]*><strong>(\d+\s*/\s*\d+\s*\(\d+%\))</strong></td>',  # В структуре таблицы
            r'<strong>(\d+\s*/\s*\d+\s*\(\d+%\))</strong>',  # В <strong>
        ]
        for pattern in score_patterns:
            match = re.search(pattern, html_body, re.IGNORECASE)
            if match:
                score_str = match.group(1).strip()
                result['score'] = score_str
                break
        
        # 5. Определяем итоговый результат по теме письма
        if subject:
            if '[Passed]' in subject:
                result['result'] = True
            elif '[Failed]' in subject:
                result['result'] = False
        
        return result
    
    def print_user_id(self, user_id: Optional[str], subject: str = ""):
        """
        Выводит User ID в консоль
        
        Args:
            user_id: User ID для вывода
            subject: Тема письма (опционально)
        """
        if user_id:
            if subject:
                logger.info(f"User ID найден: {user_id} (Тема: {subject})")
            else:
                logger.info(f"User ID найден: {user_id}")
        else:
            logger.warning("User ID не найден в письме")
    
    def find_student_by_code(self, code: str) -> Optional[Student]:
        """
        Находит студента в базе данных по коду с загрузкой группы и куратора
        
        Args:
            code: Код студента (ID пользователя из письма)
            
        Returns:
            Объект Student или None, если не найден
        """
        try:
            student = Student.objects.select_related('group', 'group__curator').get(code=code)
            logger.info(f"Студент найден по коду {code}: {student}")
            return student
        except Student.DoesNotExist:
            logger.warning(f"Студент с кодом {code} не найден в базе данных")
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска студента с кодом {code}: {e}")
            return None
    
    def find_curator_for_student(self, student: Student) -> Optional[User]:
        """
        Находит куратора группы студента
        
        Args:
            student: Объект Student
            
        Returns:
            Объект User (куратор) или None, если куратор не найден
        """
        if not student.group:
            logger.warning(f"У студента {student} нет группы")
            return None
        
        curator = student.group.curator
        if not curator:
            logger.warning(f"У группы {student.group} нет куратора")
            return None
        
        logger.info(f"Куратор найден для студента {student}: {curator}")
        return curator
    
    def get_curator_email(self, student: Student) -> Optional[str]:
        """
        Получает email куратора группы студента, если у куратора включен флаг send_emails
        
        Args:
            student: Объект Student
            
        Returns:
            Email куратора или None, если куратор не найден или send_emails=False
        """
        curator = self.find_curator_for_student(student)
        if not curator:
            logger.info(f"Куратор не найден для студента {student}, письмо не будет переслано")
            return None
        
        if not curator.send_emails:
            logger.info(f"У куратора {curator} отключен флаг send_emails, письмо не будет переслано")
            return None
        
        email = curator.email
        if not email:
            logger.warning(f"У куратора {curator} не указан email")
            return None
        
        logger.info(f"Email куратора найден: {email} (куратор: {curator})")
        return email
    
    def connect_imap(self) -> Optional[imaplib.IMAP4_SSL]:
        """Подключение к IMAP серверу"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            logger.info(f"Успешное подключение к IMAP: {self.imap_server}")
            return mail
        except Exception as e:
            logger.error(f"Ошибка подключения к IMAP: {e}")
            return None
    
    def connect_smtp(self) -> Optional[smtplib.SMTP]:
        """Подключение к SMTP серверу"""
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.email_address, self.email_password)
            logger.info(f"Успешное подключение к SMTP: {self.smtp_server}")
            return server
        except Exception as e:
            logger.error(f"Ошибка подключения к SMTP: {e}")
            return None
    
    def get_new_emails(self, mail: imaplib.IMAP4_SSL) -> list:
        """Получение списка новых писем"""
        try:
            mail.select('INBOX')
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            for email_id in email_ids:
                uid = email_id.decode('utf-8')
                if uid not in self.processed_uids:
                    new_emails.append(uid)
                    self.processed_uids.add(uid)
            
            return new_emails
        except Exception as e:
            logger.error(f"Ошибка получения списка писем: {e}")
            return []
    
    def fetch_email(self, mail: imaplib.IMAP4_SSL, email_id: str) -> Optional[email.message.Message]:
        """Получение содержимого письма"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                return None
            
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            return email_message
        except Exception as e:
            logger.error(f"Ошибка получения письма {email_id}: {e}")
            return None
    
    def forward_email(self, smtp: smtplib.SMTP, email_message: email.message.Message, recipient_emails: Optional[List[str]] = None) -> bool:
        """Пересылка письма"""
        try:
            # Получаем информацию о письме
            subject = self.decode_mime_words(email_message.get('Subject', 'Без темы'))
            from_addr = self.decode_mime_words(email_message.get('From', 'Неизвестно'))
            date = email_message.get('Date', '')
            
            # Извлекаем текстовую и HTML версии письма
            text_body = None
            html_body = None
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Пропускаем вложения
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain" and text_body is None:
                        try:
                            text_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
                    elif content_type == "text/html" and html_body is None:
                        try:
                            html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
            else:
                # Простое письмо без multipart
                content_type = email_message.get_content_type()
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    if content_type == "text/html":
                        html_body = body
                    else:
                        text_body = body
                except:
                    pass
            
            # Определяем адреса для пересылки
            if recipient_emails and len(recipient_emails) > 0:
                # Используем переданные адреса
                to_addresses = recipient_emails
                logger.info(f"Пересылка на адреса: {', '.join(to_addresses)}")
            else:
                # Нет получателей - не пересылаем письмо
                logger.info("Письмо не переслано: нет получателей")
                return False
            
            # Создаем multipart/alternative сообщение
            forwarded_msg = MIMEMultipart('alternative')
            
            # Устанавливаем заголовки
            forwarded_msg['From'] = self.email_address
            forwarded_msg['To'] = ', '.join(to_addresses)  # Несколько адресов через запятую
            forwarded_msg['Subject'] = f"Fwd: {subject}"
            
            # Формируем заголовок для пересылки
            header_text = f"Пересланное письмо\nОт: {from_addr}\nДата: {date}\nТема: {subject}\n\n{'=' * 50}\n\n"
            header_html = f"""<div style="font-family: Arial, sans-serif; padding: 10px; border-bottom: 2px solid #ccc; margin-bottom: 20px;">
                <p><strong>Пересланное письмо</strong></p>
                <p><strong>От:</strong> {from_addr}</p>
                <p><strong>Дата:</strong> {date}</p>
                <p><strong>Тема:</strong> {subject}</p>
            </div>"""
            
            # Добавляем текстовую версию (если есть)
            if text_body:
                full_text = header_text + text_body
                text_part = MIMEText(full_text, 'plain', 'utf-8')
                forwarded_msg.attach(text_part)
            elif html_body:
                # Если есть только HTML, создаем простую текстовую версию
                full_text = header_text + "Это письмо доступно только в HTML формате."
                text_part = MIMEText(full_text, 'plain', 'utf-8')
                forwarded_msg.attach(text_part)
            
            # Добавляем HTML версию (если есть)
            if html_body:
                full_html = header_html + html_body
                html_part = MIMEText(full_html, 'html', 'utf-8')
                forwarded_msg.attach(html_part)
            elif text_body:
                # Если есть только текст, создаем простую HTML версию
                full_html = header_html + f"<pre style='white-space: pre-wrap; font-family: Arial, sans-serif;'>{text_body}</pre>"
                html_part = MIMEText(full_html, 'html', 'utf-8')
                forwarded_msg.attach(html_part)
            
            # Отправляем письмо на все указанные адреса
            smtp.send_message(forwarded_msg, to_addrs=to_addresses)
            logger.info(f"Письмо переслано на {len(to_addresses)} адрес(ов): {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка пересылки письма: {e}")
            return False
    
    def process_emails(self):
        """Основной цикл обработки писем"""
        logger.info("Запуск мониторинга почты...")
        
        while True:
            try:
                # Подключаемся к IMAP
                mail = self.connect_imap()
                if not mail:
                    time.sleep(60)  # Ждем минуту перед повторной попыткой
                    continue
                
                # Получаем новые письма
                new_emails = self.get_new_emails(mail)
                
                if new_emails:
                    logger.info(f"Найдено новых писем: {len(new_emails)}")
                    
                    # Подключаемся к SMTP
                    smtp = self.connect_smtp()
                    if not smtp:
                        mail.close()
                        mail.logout()
                        time.sleep(60)
                        continue
                    
                    # Обрабатываем каждое письмо
                    for email_id in new_emails:
                        email_message = self.fetch_email(mail, email_id)
                        if email_message:
                            # Извлекаем текстовую и HTML версии для парсинга User ID
                            text_body = None
                            html_body = None
                            
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition", ""))
                                    if "attachment" in content_disposition:
                                        continue
                                    if content_type == "text/plain" and text_body is None:
                                        try:
                                            text_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        except:
                                            pass
                                    elif content_type == "text/html" and html_body is None:
                                        try:
                                            html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        except:
                                            pass
                            else:
                                content_type = email_message.get_content_type()
                                try:
                                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    if content_type == "text/html":
                                        html_body = body
                                    else:
                                        text_body = body
                                except:
                                    pass
                            
                            # Получаем тему письма
                            subject = self.decode_mime_words(email_message.get('Subject', ''))
                            
                            # Парсим HTML письма для извлечения структурированных данных
                            parsed_data = self.parse_email_html(html_body, subject)
                            print(f"Распарсенные данные из HTML: {parsed_data}")
                            
                            # Сохраняем результат в базу данных
                            if parsed_data.get('user_id') and parsed_data.get('task_code'):
                                logger.info(f"Вызов save_quiz_result() с данными: user_id={parsed_data.get('user_id')}, task_code={parsed_data.get('task_code')}")
                                save_result = save_quiz_result(parsed_data, html_body)
                                if save_result:
                                    logger.info("Результат успешно сохранен в базу данных")
                                else:
                                    logger.warning("Не удалось сохранить результат в базу данных")
                            else:
                                missing_fields = []
                                if not parsed_data.get('user_id'):
                                    missing_fields.append('user_id')
                                if not parsed_data.get('task_code'):
                                    missing_fields.append('task_code')
                                logger.warning(f"Пропуск сохранения в базу данных: отсутствуют поля {', '.join(missing_fields)}")
                            
                            # Парсим User ID
                            user_id = self.parse_user_id(text_body, html_body)
                            self.print_user_id(user_id, subject)
                            
                            # Если найден user_id, пытаемся найти студента по code и получить email куратора
                            curator_email = None
                            if user_id:
                                student = self.find_student_by_code(user_id)
                                if student:
                                    logger.info(f"Используем код студента {student.code} для обработки")
                                    curator_email = self.get_curator_email(student)
                                    if curator_email:
                                        logger.info(f"Письмо будет переслано куратору: {curator_email}")
                                    else:
                                        logger.info("Письмо не будет переслано: куратор не найден или send_emails=False")
                            
                            # Пересылаем письмо только если найден email куратора
                            if curator_email:
                                self.forward_email(smtp, email_message, [curator_email])
                            else:
                                logger.info("Письмо не переслано: нет получателя (куратор не найден или send_emails=False)")
                    
                    # Закрываем соединения
                    smtp.quit()
                
                mail.close()
                mail.logout()
                
                # Ждем перед следующей проверкой
                time.sleep(30)  # Проверяем каждые 30 секунд
                
            except KeyboardInterrupt:
                logger.info("Остановка мониторинга...")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)


def main():
    """
    Основная функция для запуска как отдельного скрипта.
    В Django контексте используется автоматический запуск через AppConfig.
    """
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения из .env файла
    load_dotenv()
    
    # Настройки из переменных окружения
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    
    # Ваши учетные данные из .env файла
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    FORWARD_TO = os.getenv('FORWARD_TO')
    
    # Проверка обязательных параметров
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not FORWARD_TO:
        logger.error("Ошибка: Не указаны обязательные параметры в .env файле!")
        logger.error("Необходимо указать: EMAIL_ADDRESS, EMAIL_PASSWORD, FORWARD_TO")
        return
    
    # USE_TLS по умолчанию True для порта 587
    USE_TLS = os.getenv('USE_TLS', 'true').lower() == 'true'
    
    # Создаем экземпляр пересылки
    forwarder = EmailForwarder(
        imap_server=IMAP_SERVER,
        imap_port=IMAP_PORT,
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        email_address=EMAIL_ADDRESS,
        email_password=EMAIL_PASSWORD,
        forward_to=FORWARD_TO,
        use_tls=USE_TLS
    )
    
    # Запускаем обработку
    forwarder.process_emails()


if __name__ == '__main__':
    main()

