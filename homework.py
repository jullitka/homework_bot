from http import HTTPStatus
import json
import logging
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram

import constants as c
from exception import RequestException, ResponseException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


handler = logging.FileHandler(filename='main.log', encoding='utf-8')
logging.basicConfig(
    handlers=(handler,),
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)


def check_tokens():
    """.
    Проверяет доступность переменных окружения, которые необходимы
    для работы программы. Если отсутствует хотя бы одна переменная
    окружения — продолжать работу бота нет смысла.
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """.
    Отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug('Сообщение отправлено')
    except Exception as error:
        logger.error(f'Ошибка при отправке {error}')


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise ResponseException(c.STATUS_CODE_ERROR_TEXT)
        response = response.json()
    except json.JSONDecodeError:
        raise json.JSONDecodeError(c.JSON_ERROR_TEXT)
    except requests.RequestException:
        raise RequestException(c.REQUEST_ERROR_TEXT)
    return response


def check_response(response):
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if type(response) is not dict:
        raise TypeError(c.TYPE_ERROR_DICT_TEXT)
    if 'homeworks' not in response:
        raise KeyError(c.KEY_HOMEWORKS_ERROR_TEXT)
    homeworks = response['homeworks']
    if type(homeworks) is not list:
        raise TypeError(c.TYPE_ERROR_LIST_TEXT)
    if not homeworks:
        raise IndexError(c.INDEX_ERROR_TEXT)
    return homeworks


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент
    из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки
    в Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    """
    if 'status' not in homework:
        raise KeyError(c.KEY_ERROR_TEXT_STATUS)
    if 'homework_name' not in homework:
        raise KeyError(c.KEY_ERROR_TEXT_HOMEWORK_NAME)
    status = homework['status']
    homework_name = homework['homework_name']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(c.KEY_ERROR_TEXT_VERDICT)
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())
        last_message = ''
        last_error = ''
    else:
        logger.critical(c.TOKENS_ERROR_TEXT)
        raise ValueError(c.TOKENS_ERROR_TEXT)

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            homework = homeworks[0]
            message = parse_status(homework)
            if last_message != message:
                send_message(bot, message)
                last_message = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if last_error != message:
                send_message(bot, message)
                last_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
