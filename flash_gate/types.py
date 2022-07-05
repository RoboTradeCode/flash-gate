from typing import Any
from typing import TypedDict
from .enums import EventType, EventAction, EventNode


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
