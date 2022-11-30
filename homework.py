import json
import logging
import os
import requests
import sys
import telegram
import time

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


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
    ERROR_TEXT = 'Недоступна одна или несколько переменных окружения'
    if (
        PRACTICUM_TOKEN
        and TELEGRAM_TOKEN
        and TELEGRAM_CHAT_ID
    ):
        return True
    else:
        logger.critical(ERROR_TEXT)
        raise Exception(ERROR_TEXT)


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
    ERROR_TEXT = 'Нет доступа к ENDPOINT'
    JSON_ERROR_TEXT = 'Данные не соответстуют json'
    STATUS_CODE_ERROR_TEXT = 'Ошибка ответа API: status_code != HTTPStatus.OK'
    REQUEST_ERROR_TEXT = 'Ошибка ответа API: RequestException '
    params = {'from_date': timestamp}
    if ENDPOINT:
        try:
            response = requests.get(
                ENDPOINT,
                headers=HEADERS,
                params=params
            )
            if response.status_code != HTTPStatus.OK:
                logger.error(STATUS_CODE_ERROR_TEXT)
                raise Exception(STATUS_CODE_ERROR_TEXT)
            response = response.json()
        except json.JSONDecodeError:
            logger.error(JSON_ERROR_TEXT)
            raise json.JSONDecodeError(JSON_ERROR_TEXT)
        except requests.RequestException:
            logger.error(REQUEST_ERROR_TEXT)
            raise Exception(REQUEST_ERROR_TEXT)
        return response
    logger.critical(ERROR_TEXT)
    raise Exception(ERROR_TEXT)


def check_response(response):
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    TYPE_ERROR_DICT_TEXT = 'Данные не соответствуют ожидаемым. Ожидается dict'
    TYPE_ERROR_LIST_TEXT = 'Данные не соответствуют ожидаемым. Ожидается list'
    KEY_ERROR_TEXT = 'Отсутствует ключ "homeworks"'
    INDEX_ERROR_TEXT = 'В списке нет работ c обновленным статусом'
    if type(response) is not dict:
        logger.error(TYPE_ERROR_DICT_TEXT)
        raise TypeError(TYPE_ERROR_DICT_TEXT)
    try:
        homeworks = response['homeworks']
        if type(homeworks) is not list:
            logger.error(TYPE_ERROR_LIST_TEXT)
            raise TypeError(TYPE_ERROR_LIST_TEXT)
        homework = homeworks[0]
        return homework
    except KeyError:
        logger.error(KEY_ERROR_TEXT)
        raise KeyError(KEY_ERROR_TEXT)
    except IndexError:
        logger.error(INDEX_ERROR_TEXT)
        raise IndexError(INDEX_ERROR_TEXT)


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент
    из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки
    в Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    """
    KEY_ERROR_TEXT = 'Отсутствует ключ "status" или "homework_name"'
    KEY_ERROR_TEXT_VERDICT = 'Неизвестный статус проверки'
    try:
        status = homework['status']
        homework_name = homework['homework_name']
    except KeyError:
        logger.error(KEY_ERROR_TEXT)
        raise KeyError(KEY_ERROR_TEXT)
    try:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        logger.error(KEY_ERROR_TEXT_VERDICT)
        raise KeyError(KEY_ERROR_TEXT_VERDICT)


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    last_error = ''

    while check_tokens():
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if last_message != message:
                send_message(bot, message)
                last_message = message
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if last_error != message:
                send_message(bot, message)
                last_error = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
