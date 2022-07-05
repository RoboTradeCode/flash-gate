from .types import Event, EventAction
from aeron import Publisher, Subscriber
from aeron.concurrent import AsyncSleepingIdleStrategy
import aeron
from typing import Callable, NoReturn
from .formatters import JsonFormatter
import logging

IDLE_SLEEP_MS = 1


class AeronConnector:
    def __init__(self, config: dict, handler: Callable[[str], None]):
        aeron_config: dict = config["data"]["configs"]["gate_config"]["aeron"]
        subscribers: dict = aeron_config["subscribers"]
        publishers: dict = aeron_config["publishers"]

        self.subscriber = Subscriber(handler, **subscribers["core"])
        self.orderbooks = Publisher(**publishers["orderbooks"])
        self.balances = Publisher(**publishers["balances"])
        self.core = Publisher(**publishers["core"])
        self.logs = Publisher(**publishers["logs"])

        self.logger = logging.getLogger(__name__)
        self.formatter = JsonFormatter(config)
        self.idle_strategy = AsyncSleepingIdleStrategy(IDLE_SLEEP_MS)

    async def run(self) -> NoReturn:
        while True:
            await self._poll()

    async def _poll(self) -> None:
        fragments_read = self.subscriber.poll()
        await self.idle_strategy.idle(fragments_read)

    def offer(self, event: Event, log=True, only_log=False) -> None:
        try:
            if not only_log:
                publisher = self._get_publisher(event)
                message = self.formatter.format(event)
                self._offer_while_not_successful(publisher, message)

            if log:
                message = self.formatter.format(event)
                self._offer_while_not_successful(self.logs, message)
        except Exception as e:
            self.logger.error(e)

    def _get_publisher(self, event: Event) -> Publisher:
        match event["action"]:
            case EventAction.ORDER_BOOK_UPDATE:
                return self.orderbooks
            case EventAction.BALANCE_UPDATE | EventAction.GET_BALANCE:
                return self.balances
            case EventAction.CREATE_ORDERS | EventAction.GET_ORDERS | EventAction.ORDERS_UPDATE:
                return self.core
            case _:
                return self.logs

    def _offer_while_not_successful(self, publisher: Publisher, message: str) -> None:
        while True:
            try:
                self._offer(publisher, message)
                break
            except aeron.AeronPublicationNotConnectedError as e:
                self.logger.warning(e)
                break
            except aeron.AeronPublicationAdminActionError as e:
                self.logger.warning(e)

    def _offer(self, publisher: Publisher, message: str) -> None:
        self.logger.info("Offering message: %s", message)
        publisher.offer(message)

    def close(self):
        self.subscriber.close()
        self.orderbooks.close()
        self.balances.close()
        self.core.close()
        self.logs.close()
