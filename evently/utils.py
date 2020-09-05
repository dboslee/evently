import asyncio
import concurrent
import logging
from typing import (
    Any,
    Callable
)

_LOGGER = logging.getLogger(__name__)


def run_callback_threadsafe(
    loop: asyncio.AbstractEventLoop, func: Callable, *args: Any
) -> concurrent.futures.Future:
    """Send a callback to a given event loop.

    Returns a future.
    """
    future = concurrent.futures.Future()

    def callback():
        try:
            future.set_result(func(*args))
        except Exception as ex:
            if future.set_running_or_notify_cancel():
                future.set_exception(ex)
            else:
                _LOGGER.warning("Exception on future: ", exc_info=True)

    loop.call_soon_threadsafe(callback)
    return future
