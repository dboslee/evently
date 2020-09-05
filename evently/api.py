from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union
)
import asyncio
import logging
from evently.utils import run_callback_threadsafe

_LOGGER = logging.getLogger(__name__)
ALL_EVENTS = "evently_all_events"


class Event:
    """Represents an event that is published over evently."""

    __slots__ = ["event_type", "event_data"]

    def __init__(self, event_type: str, event_data: Optional[Any]):
        self.event_type = event_type
        self.event_data = event_data

    def __repr__(self) -> str:
        return "<Event %s>" % self.event_type


class EventHandler:
    """Wraps a function subscribed to an event_type."""

    def __init__(
        self,
        evently: "Evently",
        event_type: Union[str, List[str]],
        event_handler: Callable,
        context: bool = False,
        blocking: bool = False
    ) -> None:
        self.evently = evently
        self.event_type = event_type
        self.event_handler = event_handler
        self.name = f"{self.event_handler.__module__}.{self.event_handler.__name__}"
        self.context = context
        self.blocking = blocking

    def unsubscribe(self) -> None:
        """Removes the handler from the evently instance."""
        self.evently.unsubscribe(self)

    def unsubscribe_threadsafe(self):
        return run_callback_threadsafe(self.evently._loop, self.unsubscribe)

    def __call__(self, event: Event) -> Any:
        if self.context:
            return self.event_handler(event, context=self)

        return self.event_handler(event)

    def __repr__(self) -> str:
        return f"<EventHandler {self.name}>"


class Evently:
    """A simple interface for publishing and subscribing to events."""

    def __init__(self, loop: asyncio.AbstractEventLoop = None) -> None:
        self._loop = loop if loop else asyncio.get_event_loop()
        self._handlers: Dict[str, Callable] = {}

    def handlers(self) -> Dict[str, Callable]:
        """Returns a mapping of event_types to event_handlers."""
        return self._handlers

    def handlers_threadsafe(self) -> Dict[str, Callable]:
        return run_callback_threadsafe(self._loop, self.handlers).result()

    def subscribe(
        self,
        event_type: Union[str, List[str]],
        context: bool = False,
        blocking: bool = False
    ) -> Callable[[Callable[..., Any]], EventHandler]:
        """Add handler to be called when an event type is published."""
        def event_handler_wrapper(func: Callable):
            event_handler = EventHandler(
                evently=self,
                event_type=event_type,
                event_handler=func,
                context=context,
                blocking=blocking
            )
            self.register_event_handler(event_type, event_handler)
            return event_handler

        return event_handler_wrapper

    def subscribe_threadsafe(
        self,
        event_type: Union[str, List[str]],
        context: bool = False,
        blocking: bool = False
    ) -> EventHandler:
        """Add handler to be called when an event type is published."""
        return run_callback_threadsafe(
            self._loop, self.subscribe, event_type, context, blocking
        ).result()

    def register_event_handler(
        self, event_type: Union[str, List[str]], event_handler: EventHandler
    ) -> None:
        """Register a given given handler with the given event_type."""
        if isinstance(event_type, str):
            self._register_event_handler(event_type, event_handler)
        elif isinstance(event_type, list):
            for event in event_type:
                self._register_event_handler(event, event_handler)
        else:
            raise ValueError(f"Failed to register {event_handler} \
                invalid event_type {type(event_type)}")

    def _register_event_handler(self, event_type: str, event_handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if event_handler not in self._handlers[event_type]:
            self._handlers[event_type].append(event_handler)
        else:
            _LOGGER.warning("Event handler already registered %s", event_handler)

    def publish(self, event_type: str, event_data: Optional[Any] = None) -> None:
        """Publish an event to any handlers subscribered."""
        event = Event(event_type, event_data)
        handlers = self._handlers.get(event_type, [])
        if event_type != ALL_EVENTS:
            handlers += self._handlers.get(ALL_EVENTS, [])

        for event_handler in handlers:
            self._execute_event_handler(event_handler, event)

    def publish_threadsafe(
        self, event_type: str, event_data: Optional[Any] = None
    ) -> None:
        """Publish an event to any handlers subscribered."""
        return run_callback_threadsafe(
            self._loop, self.publish, event_type, event_data
        ).result()

    def unsubscribe(self, event_handler: EventHandler) -> None:
        """Remove the given handler from all events."""
        event_type = event_handler.event_type
        if isinstance(event_type, list):
            for event in event_type:
                self._unsubscribe(event, event_handler)
        elif isinstance(event_type, str):
            self._unsubscribe(event_type, event_handler)

    def unsubscribe_threadsafe(self, event_handler: EventHandler) -> None:
        """Remove the given handler from all events."""
        return run_callback_threadsafe(
            self._loop, self.unsubscribe, event_handler
        ).result()

    def _unsubscribe(self, event_type: str, event_handler: EventHandler) -> None:
        try:
            self._handlers[event_type].remove(event_handler)
        except (KeyError, ValueError):
            _LOGGER.warning(
                "Unable to remove unknown event handler %s %s",
                event_type,
                event_handler
            )
        # Remove the event type if there are no more subscribers
        try:
            if not self._handlers[event_type]:
                self._handlers.pop(event_type)
        except KeyError:
            pass

    def _execute_event_handler(
        self, event_handler: EventHandler, event: Event
    ) -> None:
        """Execute the subscriber as a callback, coroutine, or thread."""
        if asyncio.iscoroutine(event_handler.event_handler):
            self._loop.create_task(event_handler.event_handler(event))
        elif asyncio.iscoroutinefunction(event_handler.event_handler):
            self._loop.create_task(event_handler.event_handler(event))
        elif event_handler.blocking:
            self._loop.run_in_executor(None, event_handler.event_handler, event)
        else:
            self._loop.call_soon(event_handler, event)
