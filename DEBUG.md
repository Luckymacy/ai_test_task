# DEBUG

## Помилка 1

Команда:
python3 app/main.py

Текст помилки:
BOT_TOKEN is not set

Причина:
У файлі .env не був вказаний токен Telegram-бота.

Виправлення:
Додано BOT_TOKEN у файл .env. Файл .env доданий у .gitignore і не потрапляє в GitHub.

## Помилка 2

Команда:
docker compose up --build

Текст помилки:
Бот не запускається або не бачить BOT_TOKEN.

Причина:
Docker Compose не отримував змінні середовища з файлу .env.

Виправлення:
У docker-compose.yml додано env_file:
- .env

## Помилка 3

Команда:
python3 app/main.py

Текст помилки:
ModuleNotFoundError або відсутня потрібна бібліотека.

Причина:
Залежності проєкту не були встановлені.

Виправлення:
Виконано:
python3 -m pip install -r requirements.txt