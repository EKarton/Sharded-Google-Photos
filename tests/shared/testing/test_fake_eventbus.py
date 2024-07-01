import unittest

from sharded_google_photos.shared.testing.fake_eventbus import FakeEventBus


class FakeEventBusTests(unittest.TestCase):

    def test_get_events_emitted__emitted_event__should_return_emitted_event(self):
        event_bus = FakeEventBus()

        event_bus.emit("test_event_name_1", 100, 1000, name="Bob")
        event_bus.emit("test_event_name_2", 20, 2000, name="Sam")

        events = event_bus.get_events_emitted()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].name, "test_event_name_1")
        self.assertEqual(events[0].args, (100, 1000))
        self.assertEqual(events[0].kwargs, {"name": "Bob"})
        self.assertEqual(events[1].name, "test_event_name_2")
        self.assertEqual(events[1].args, (20, 2000))
        self.assertEqual(events[1].kwargs, {"name": "Sam"})

    def test_get_events_emitted__with_subscribers__should_pass_event_to_subscribers(
        self,
    ):
        event_bus = FakeEventBus()
        self.captured_args = None
        self.captured_kwargs = None

        @event_bus.on("test_event_name_1")
        def subscribe_to_event(*args, **kwargs):
            self.captured_args = args
            self.captured_kwargs = kwargs

        event_bus.emit("test_event_name_1", 100, 1000, name="Bob")

        self.assertEqual(self.captured_args, (100, 1000))
        self.assertEqual(self.captured_kwargs, {"name": "Bob"})
