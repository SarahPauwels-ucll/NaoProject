import unittest
from MoodDetection import MoodDetector

class MemorySubscriberStub:

    def __init__(self):
        pass

class MyTestCase(unittest.TestCase):
    def test_init(self):

        mem_stub = MemorySubscriberStub()
        test_class = MoodDetector(mem_stub)

        self.assertIsNotNone(test_class.memory)
        self.assertIsNone(test_class.memory_subscriber)

if __name__ == '__main__':
    unittest.main()
