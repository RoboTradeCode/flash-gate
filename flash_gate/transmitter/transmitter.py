from abc import ABC


class Transmitter(ABC):
    async def poll(self):
        ...

    async def offer(self, event):
        ...


class AeronTransmitter(Transmitter):
    def __init__(self):
        ...

    def poll(self):
        return
