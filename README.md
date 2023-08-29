# homework_bot
Телеграм - бот обращается к API сервису Практикум.Домашка и узнаёт статус проверки проекта ревьером: взят ли он на проверку, проверен ли и результат проверки.

## Технологии
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)

## Запуск проекта

Клонировать репозиторий и перейти в папку с проектом:
    ```
    git clone https://github.com/jullitka/homework_bot.git
    cd homework_bot
    ```
Cоздать и активировать виртуальное окружение:

```
python -m venv env
```
Для Linux
    ```
    source venv/bin/activate
    ```
    
Для Windows
    ```
    source venv/Scripts/activate
    ```

Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Зарегистрировать чат-бота в Телеграм

Создать в корневой директории проекта файл .env со следующими переменными окружения:

```
PRAKTIKUM_TOKEN = 'xxx'
TELEGRAM_TOKEN = 'xxx'
TELEGRAM_CHAT_ID = 'xxx'
```

Запустить проект:
```
python homework_bot.py
```
