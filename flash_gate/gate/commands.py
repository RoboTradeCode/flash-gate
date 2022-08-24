from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    async def execute(self):
        ...


class CreateOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class CancelOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class CancelAllOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class GetOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class GetBalance(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...
