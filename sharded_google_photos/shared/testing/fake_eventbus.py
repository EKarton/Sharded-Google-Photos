from dataclasses import dataclass
from typing import Any

from event_bus import EventBus


@dataclass
class Event:
    """Class for keeping track of the events emitted."""

    name: str
    args: Any
    kwargs: dict[str, Any]


class FakeEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self._emitted_events: list[Event] = []

    def emit(self, event: str, *args: Any, **kwargs: dict[str, Any]) -> None:
        self._emitted_events.append(Event(event, args, kwargs))
        super().emit(event, *args, **kwargs)

    def get_events_emitted(self) -> list[Event]:
        return self._emitted_events
