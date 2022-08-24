from .enum import EventAction, EventType
from datetime import datetime
from uuid import uuid4


class EventFormatter:
    """
    Класс для форматирования результатов выполнения команд в события ответа
    """

    def __init__(self, exchange_id: str, algo: str, node: str, instance: str):
        self.exchange = exchange_id
        self.algo = algo
        self.node = node
        self.instance = instance

    def format(
        self,
        event_type: EventType,
        action: EventAction = None,
        event_id: str = None,
        message: str = None,
        data=None,
    ) -> dict:
        """
        Создать событие ответа

        Если идентификатор события не передан, будет сгенерирован UUID v4
        """
        if event_id is None:
            event_id = str(uuid4())

        response = self.template
        response["event_id"] = event_id
        response["event"] = event_type
        response["action"] = action
        response["message"] = message
        response["timestamp"] = self.timestamp_us()
        response["data"] = data

        return response

    @property
    def template(self) -> dict:
        """
        Шаблон события

        Заполнен константными значениями, которые не меняются во время работы шлюза
        """
        template = {
            "event_id": None,
            "event": None,
            "exchange": self.exchange,
            "algo": self.algo,
            "node": self.node,
            "instance": self.instance,
            "message": None,
            "action": None,
            "timestamp": None,
            "data": None,
        }
        return template

    @staticmethod
    def timestamp_us() -> int:
        """
        Получить временную метку в микросекундах (секунды * 10^6)
        """
        timestamp_s = datetime.now().timestamp()
        timestamp_us = int(timestamp_s * 1_000_000)
        return timestamp_us
