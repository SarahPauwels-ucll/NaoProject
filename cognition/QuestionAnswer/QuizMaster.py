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

STATE_IDLE = "STATE_IDLE"
STATE_START_GAME = "STATE_START_GAME"
STATE_CONTINUE = "STATE_CONTINUE"
STATE_PLAY_TRACK = "STATE_PLAY_TRACK",
STATE_ASK_QUESTION = "STATE_ASK_QUESTION",
STATE_AWAIT_ANSWER = "STATE_AWAIT_ANSWER",
STATE_EVALUATE_ANSWER = "STATE_EVALUATE_ANSWER",
STATE_FEEDBACK_SUCCESS = "STATE_FEEDBACK_SUCCESS",
STATE_FEEDBACK_FAILURE = "STATE_FEEDBACK_FAILURE",
STATE_FEEDBACK_ENCOURAGEMENT = "STATE_FEEDBACK_ENCOURAGEMENT",
STATE_FEEDBACK_TIMEOUT = "STATE_FEEDBACK_TIMEOUT",

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

        self.game_state = STATE_IDLE

    def start(self):

        self.logger.info("QuizMaster Starting")

        #self.talk_service.post.say("Yo!")
        self.playlist_manager = PlaylistManager.PlaylistManager(self.app, MUSIC_DIR)
        self.playlist_manager.initialisePlaylist()
        #title, artist = self.playlist_manager.playTrack()


        # self.listen_subscriber = session.service("ALSpeechRecognition")

        #self.memory_subscriber.signal.connect(self.on_face_detected)
        self.memory_subscriber = self.memory_service.subscriber("WordRecognized")
        self.memory_subscriber.signal.connect(self.on_word_recognised)

        self.logger.info("QuizMaster subscriptions completed")

    def stop(self):
        #if self.memory_subscriber:
        #    self.memory_subscriber.signal.disconnect(self.on_face_detected)

        #self.talk_service.stop()
        self.talk_service = None
        #raise RuntimeError()

    def on_word_recognised(self, value):

        if self.game_state == STATE_IDLE and value[0] == "start game":
            self.logger.info(type(value[0]))

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

        app.run()


    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)