from typing import Any
from typing import TypedDict
from flash_gate.gate.enums import EventType, EventAction, EventNode


class Config(TypedDict):
    exchange_id: str
    exchange_config: dict
    assets: list[str]
    symbols: list[str]
    limit: list[str]


class Message(TypedDict):
    event_id: str
    event: EventType
    action: EventAction
    message: str
    data: Any


class Event(TypedDict, total=False):
    event_id: str
    event: EventType
    exchange: str
    node: EventNode
    instance: str
    algo: str
    action: EventAction
    message: str
    timestamp: int
    data: Any
