class ResponseException(Exception):
    """Ошибка ответа API."""

    pass


class RequestException(Exception):
    """Ошибка запроса к API адресу."""

    pass


class TelegramException(Exception):
    """Ошибка отправки сообщения."""

    pass
