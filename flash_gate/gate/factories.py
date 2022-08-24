from .commands import Command
from .commands import CreateOrders, CancelOrders, CancelAllOrders, GetOrders, GetBalance
from .enum import EventAction


class SimpleCommandFactory:
    @staticmethod
    def create_command(action: EventAction) -> Command:
        match action:
            case EventAction.CREATE_ORDERS:
                command = CreateOrders()
            case EventAction.CANCEL_ORDERS:
                command = CancelOrders()
            case EventAction.CANCEL_ALL_ORDERS:
                command = CancelAllOrders()
            case EventAction.GET_ORDERS:
                command = GetOrders()
            case EventAction.GET_BALANCE:
                command = GetBalance()
            case _:
                raise ValueError(f"Unsupported command: {action}")

        return command
