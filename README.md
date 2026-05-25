# Email Forwarding Script

Автоматическая пересылка новых писем с одного почтового ящика на другой.

## Возможности

- Мониторинг почтового ящика в реальном времени
- Автоматическая пересылка новых писем
- Поддержка Gmail, Yandex, Mail.ru, Outlook и других почтовых сервисов
- Сохранение темы, отправителя и содержимого письма
- Логирование всех операций

## Установка

1. Клонируйте репозиторий или скачайте файлы проекта

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Откройте файл `.env` и заполните его своими данными

## Настройка для Gmail

1. **Включите двухфакторную аутентификацию** в вашем Google аккаунте:
   - Перейдите в [Настройки аккаунта Google](https://myaccount.google.com/)
   - Безопасность → Двухэтапная аутентификация

2. **Создайте App Password**:
   - В настройках безопасности найдите "Пароли приложений"
   - Выберите "Почта" и "Другое устройство"
   - Скопируйте созданный пароль (16 символов)
   - Используйте этот пароль в `EMAIL_PASSWORD` в файле `.env`

3. Заполните `.env` файл:
```env
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
FORWARD_TO=forward_to@example.com
USE_TLS=true
AUTO_START_EMAIL_FORWARDER=true
```

**Примечание:** `AUTO_START_EMAIL_FORWARDER` - управляет автозапуском email_forwarder при старте Django сервера. Установите `false`, чтобы отключить автозапуск (по умолчанию `true`).

## Настройка для других почтовых сервисов

### Yandex Mail

```env
IMAP_SERVER=imap.yandex.ru
IMAP_PORT=993
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=465
EMAIL_ADDRESS=your_email@yandex.ru
EMAIL_PASSWORD=your_password
FORWARD_TO=forward_to@example.com
USE_TLS=false
AUTO_START_EMAIL_FORWARDER=true
```

**Важно для Yandex**: Включите доступ по протоколу IMAP в настройках почты и создайте пароль приложения.

### Mail.ru

```env
IMAP_SERVER=imap.mail.ru
IMAP_PORT=993
SMTP_SERVER=smtp.mail.ru
SMTP_PORT=465
EMAIL_ADDRESS=your_email@mail.ru
EMAIL_PASSWORD=your_password
FORWARD_TO=forward_to@example.com
USE_TLS=false
AUTO_START_EMAIL_FORWARDER=true
```

### Outlook/Hotmail

```env
IMAP_SERVER=outlook.office365.com
IMAP_PORT=993
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
EMAIL_ADDRESS=your_email@outlook.com
EMAIL_PASSWORD=your_password
FORWARD_TO=forward_to@example.com
USE_TLS=true
AUTO_START_EMAIL_FORWARDER=true
```

## Использование

Запустите скрипт:
```bash
python email_forwarder.py
```

Скрипт будет:
- Проверять новые письма каждые 30 секунд
- Автоматически пересылать их на указанный адрес
- Выводить информацию о работе в консоль

Для остановки нажмите `Ctrl+C`.

## Запуск в фоновом режиме

### Windows

Используйте планировщик задач Windows или запустите через PowerShell:
```powershell
Start-Process python -ArgumentList "email_forwarder.py" -WindowStyle Hidden
```

### Linux/Mac

Используйте `nohup` или `screen`:
```bash
nohup python email_forwarder.py > email_forwarder.log 2>&1 &
```

Или с `screen`:
```bash
screen -S email_forwarder
python email_forwarder.py
# Нажмите Ctrl+A затем D для отсоединения
```

## Структура проекта

```
email_forwarding/
├── email_forwarder.py  # Основной скрипт
├── requirements.txt    # Зависимости Python
├── .env.example        # Пример конфигурации
├── .env                # Ваша конфигурация (создается вручную)
├── .gitignore          # Исключения для Git
└── README.md           # Документация
```

## Безопасность

- **Никогда не коммитьте файл `.env` в Git!** Он содержит ваши пароли
- Используйте App Passwords вместо обычных паролей
- Храните `.env` файл в безопасном месте
- Регулярно обновляйте пароли

## Устранение неполадок

### Ошибка подключения к IMAP/SMTP

- Проверьте правильность сервера и порта
- Убедитесь, что включен доступ по IMAP/SMTP в настройках почты
- Для Gmail используйте App Password, а не обычный пароль

### Письма не пересылаются

- Проверьте логи в консоли
- Убедитесь, что адрес `FORWARD_TO` указан правильно
- Проверьте, что в почтовом ящике есть непрочитанные письма

### Ошибка аутентификации

- Для Gmail: используйте App Password
- Для Yandex: создайте пароль приложения в настройках безопасности
- Убедитесь, что пароль скопирован полностью без пробелов

## Лицензия

Свободное использование для личных и коммерческих целей.


