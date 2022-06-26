from logging import Handler, LogRecord
import aeron
from aeron import Publisher


class AeronHandler(Handler):
    def __init__(self, channel: str, stream_id: int):
        super().__init__()
        self.publisher = Publisher(channel, stream_id)

    def emit(self, record: LogRecord):
        while True:
            try:
                self.publisher.offer(record.getMessage())
                break
            except aeron.AeronPublicationNotConnectedError:
                break
            except aeron.AeronPublicationAdminActionError:
                pass
