import asyncio
import threading
import unittest

from evently import (
    ALL_EVENTS,
    Event,
    Evently,
    EventHandler
)
from evently import utils

TEST_EVENT = "test_event"
TEST_EVENT_2 = "test_event_2"
TEST_EVENT_3 = "test_event_3"


def get_event_evently():
    loop = asyncio.new_event_loop()
    stop_event = threading.Event()

    def run_loop():
        loop.run_forever()
        stop_event.set()

    def stop_loop_threadsafe():
        async def stop_loop():
            loop.stop()

        asyncio.run_coroutine_threadsafe(stop_loop(), loop)
        stop_event.wait()
        loop.close()

    def iterate_loop_threadsafe():
        utils.run_callback_threadsafe(loop, lambda: None).result()

    threading.Thread(name="LoopThread", target=run_loop, daemon=False).start()
    evently = Evently(loop)
    evently.stop_loop_threadsafe = stop_loop_threadsafe
    evently.iterate_loop_threadsafe = iterate_loop_threadsafe
    return evently


class TestEventlyThreadsafe(unittest.TestCase):

    def setUp(self):
        self.evently = get_event_evently()

    def tearDown(self):
        self.evently.stop_loop_threadsafe()

    def test_get_subscribers_threadsafe(self):
        assert self.evently.handlers_threadsafe() == {}

    def test_subscribe_decorator_threadsafe(self):
        calls = 0

        @self.evently.subscribe_threadsafe(TEST_EVENT)
        def event_handler(event: Event):
            nonlocal calls
            calls += 1

        print(event_handler)

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

    def test_subscribe_with_context(self):
        calls = 0
        handler = None

        @self.evently.subscribe_threadsafe(TEST_EVENT, context=True)
        def event_handler(event: Event, context: EventHandler):
            nonlocal calls, handler
            calls += 1
            handler = context

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1
        assert isinstance(handler, EventHandler)

    def test_subscribe_all(self):
        calls = 0

        @self.evently.subscribe_threadsafe(ALL_EVENTS)
        def event_handler(event: Event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

    def test_subscribe_multiple(self):
        calls = 0

        @self.evently.subscribe_threadsafe([TEST_EVENT, TEST_EVENT_2])
        def event_handler(event: Event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

        self.evently.publish_threadsafe(TEST_EVENT_2)
        self.evently.iterate_loop_threadsafe()
        assert calls == 2

        self.evently.publish_threadsafe(TEST_EVENT_3)
        self.evently.iterate_loop_threadsafe()
        assert calls == 2

    def test_unsubscribe(self):
        calls = 0

        @self.evently.subscribe_threadsafe(TEST_EVENT)
        def test1(event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

        self.evently.unsubscribe_threadsafe(test1)

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

    def test_handler_unsubscriber(self):
        calls = 0

        @self.evently.subscribe_threadsafe(TEST_EVENT)
        def test1(event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

        test1.unsubscribe_threadsafe()

        assert self.evently.handlers_threadsafe() == {}
        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

    def test_coro_handler(self):
        calls = 0

        @self.evently.subscribe_threadsafe(TEST_EVENT)
        async def coro_handler(event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1

    def test_thread_handler(self):
        calls = 0

        @self.evently.subscribe_threadsafe(TEST_EVENT, blocking=True)
        def thread_handler(event):
            nonlocal calls
            calls += 1

        self.evently.publish_threadsafe(TEST_EVENT)
        self.evently.iterate_loop_threadsafe()
        assert calls == 1


if __name__ == "__main__":
    unittest.main()
