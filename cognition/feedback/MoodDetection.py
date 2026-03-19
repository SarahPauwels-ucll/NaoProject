ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "51988"

proxies = ["ALFaceDetection", "ALMemory"]

class MoodDetector:

    def __init__(self, memory):

        self.memory = memory
        self.memory_subscriber = None

    def start(self):
        self.memory_subscriber = self.memory.subscribe("FaceDetected")
        self.memory_subscriber.signal.connect(self.on_face_detected)

    def stop(self):
        if self.memory_subscriber:
            self.memory_subscriber.signal.disconnect(self.on_face_detected)

    def on_face_detected(self, value):
        print value


if __name__ == "__main__":

    import sys
    import qi

    try:
        app = qi.Application()
        app.start()
        memory = app.session.service(proxies[1])
        moodDetector = MoodDetector(app)
        moodDetector.run()

    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)