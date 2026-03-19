import unittest
from MoodDetection import MoodDetector

class SignalStub:

    def __init__(self):

        self.callback = None

    def connect(self, callback):

        self.callback = callback

    def disconnect(self, callback):

        self.callback = None

    def notify_fail(self):

        self.callback([])

    def notify_happy(self):

        self.callback([0.5, 0.5, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7])

class MemorySubscriberStub:

    def __init__(self):

        self.signal = SignalStub()

    def subscribe(self, event_name):

        return self


class MyTestCase(unittest.TestCase):

    def test_init(self):

        mem_stub = MemorySubscriberStub()
        test_class = MoodDetector(mem_stub)

        self.assertIsNotNone(test_class.memory)
        self.assertIsNone(test_class.memory_subscriber)
        self.assertFalse(test_class.got_face)

    def test_callback_fail(self):

        mem_stub = MemorySubscriberStub()
        test_class = MoodDetector(mem_stub)
        test_class.start()

        test_class.memory_subscriber.signal.notify_fail()

        self.assertFalse(test_class.got_face)

    def test_callback_success(self):

        mem_stub = MemorySubscriberStub()
        test_class = MoodDetector(mem_stub)
        test_class.start()

        test_class.memory_subscriber.signal.notify_happy()

        self.assertTrue(test_class.got_face)

if __name__ == '__main__':
    unittest.main()
