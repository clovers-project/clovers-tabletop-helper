from typing import Protocol
from collections.abc import Sequence


class PropertiesProtocol(Protocol):
    user_id: str
    group_id: str | None
    permission: int


class Event(PropertiesProtocol, Protocol):

    message: str
    args: Sequence[str]
    properties: dict

    def call(self, key: str, *args): ...
