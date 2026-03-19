import sys

import qi
from naoqi import  ALProxy

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "51988"

proxies = ["ALFaceDetection", "ALMemory"]

class MoodDetector(object):

    def __init__(self, app):

        super().__init__()

        app.start()
        self.session = app.session()
        self.memory = ALProxy(proxies[1])
        self.memory_subscriber = self.memory.subscribe("FaceDetected")
        self.memory_subscriber.signal.connect(self.on_face_detected)

    def on_face_detected(self, value):
        pass


if __name__ == "__main__":

    try:
        connection_string = "tcp://" + ROBOT_IP + ":" + ROBOT_PORT
        app = qi.Application()

        moodDetector = MoodDetector(app)
    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)

    detector = MoodDetector(app)
    detector.run()