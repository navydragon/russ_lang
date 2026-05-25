from django.apps import AppConfig
import logging
import threading
import os
import sys

logger = logging.getLogger(__name__)


class ForwarderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forwarder'
    
    def ready(self):
        """
        Запускает email_forwarder в отдельном потоке при старте Django.
        Запускается только один раз при старте сервера.
        """
        # Проверяем, включен ли автозапуск через переменную окружения
        auto_start = os.getenv('AUTO_START_EMAIL_FORWARDER', 'true').lower() == 'true'
        if not auto_start:
            logger.info("Автозапуск email_forwarder отключен (AUTO_START_EMAIL_FORWARDER=false)")
            return
        
        # Пропускаем запуск при выполнении команд управления Django
        if len(sys.argv) > 1:
            command = sys.argv[1]
            # Не запускаем при миграциях, collectstatic и других командах управления
            if command in ['migrate', 'makemigrations', 'collectstatic', 'test', 'shell', 'dbshell']:
                return
        
        # Проверяем, что мы в основном процессе (для runserver)
        # RUN_MAIN устанавливается только в основном процессе runserver
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from .email_forwarder import EmailForwarder
        
        # Проверяем наличие обязательных переменных окружения
        email_address = os.getenv('EMAIL_ADDRESS')
        email_password = os.getenv('EMAIL_PASSWORD')
        forward_to = os.getenv('FORWARD_TO')
        
        if not email_address or not email_password or not forward_to:
            logger.warning(
                "Email forwarder не запущен: отсутствуют обязательные параметры в .env файле. "
                "Необходимо указать: EMAIL_ADDRESS, EMAIL_PASSWORD, FORWARD_TO"
            )
            return
        
        # Запускаем forwarder в отдельном потоке
        def start_forwarder():
            try:
                imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
                imap_port = int(os.getenv('IMAP_PORT', '993'))
                smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
                smtp_port = int(os.getenv('SMTP_PORT', '587'))
                use_tls = os.getenv('USE_TLS', 'true').lower() == 'true'
                
                forwarder = EmailForwarder(
                    imap_server=imap_server,
                    imap_port=imap_port,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    email_address=email_address,
                    email_password=email_password,
                    forward_to=forward_to,
                    use_tls=use_tls
                )
                
                logger.info("Запуск email_forwarder в фоновом режиме...")
                forwarder.process_emails()
            except Exception as e:
                logger.error(f"Ошибка при запуске email_forwarder: {e}", exc_info=True)
        
        # Создаем и запускаем поток
        forwarder_thread = threading.Thread(target=start_forwarder, daemon=True)
        forwarder_thread.start()
        logger.info("Email forwarder запущен в фоновом потоке")

