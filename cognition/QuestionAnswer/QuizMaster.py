import qi
import PlaylistManager

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "52815"

proxies = [
    "ALTextToSpeech",
    "ALSpeechRecognition",
    "ALMemory",
    "ALLogger",
]

#MUSIC_DIR = "/home/nao/music"
MUSIC_DIR = "C:/GitRepos/ENG7007_PRAC1_GROUP/NaoProject/cognition/music_quiz/music"

class QuizMaster(object):

    def __init__(self, app, talk, listen, remember):

        self.app = app

        self.playlist_manager = None

        self.talk_service = talk
        self.listen_service = listen

        self.memory_service = remember
        self.memory_subscriber = None

        self.logger = qi.Logger("QuizMaster")

    def start(self):

        self.logger.info("Here!")

        #self.talk_service.post.say("Yo!")
        self.playlist_manager = PlaylistManager.PlaylistManager(self.app, MUSIC_DIR)
        self.playlist_manager.initialisePlaylist()
        title, artist = self.playlist_manager.playTrack()


        # self.listen_subscriber = session.service("ALSpeechRecognition")
        #self.memory = self.app.service("ALMemory")
        #self.memory_subscriber.signal.connect(self.on_face_detected)

    def stop(self):
        #if self.memory_subscriber:
        #    self.memory_subscriber.signal.disconnect(self.on_face_detected)

        #self.talk_service.stop()
        self.talk_service = None
        raise RuntimeError()

if __name__ == "__main__":

    import sys
    import qi

    try:
        app = qi.Application()
        app.start()

        talk = app.session.service(proxies[0])
        listen = None # app.session.service(proxies[1])
        remember = app.session.service(proxies[2])

        quiz_master = QuizMaster(app, talk, listen, remember)
        quiz_master.start()

        #app.run()


    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)