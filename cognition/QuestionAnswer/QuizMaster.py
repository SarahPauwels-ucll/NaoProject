import sys
import qi
import random
import threading
import PlaylistManager

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "64286"
#ROBOT_IP = "172.18.16.47"
#ROBOT_PORT = "9559"

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
        self.listen = listen

        self.memory_service = remember
        self.memory_subscriber = None

        self.logger = qi.Logger("QuizMaster")

        self.game_state = STATE_IDLE
        self.state_lock = threading.Lock()

        self.answer_timer = None
        self.feedback_lock = threading.Lock()

    def start(self):

        self.logger.info("QuizMaster Starting")

        self.playlist_manager = PlaylistManager.PlaylistManager(self.app, MUSIC_DIR)
        self.playlist_manager.initialisePlaylist()

        # isSrAvailable = True
        # try:
        #     self.listen = app.session.service("ALSpeechRecognition")
        #     self.listen.pause(True)
        # except:
        #     self.logger.error("Failed to get a handle to ALSpeechRecognition, defaulting to Virtual Robot Test Mode")
        #     isSrAvailable = False

        #self.memory_subscriber.signal.connect(self.on_face_detected)
        self.memory_subscriber = self.memory_service.subscriber("WordRecognized")
        self.memory_subscriber.signal.connect(self.on_word_recognised)

        self.logger.info("QuizMaster subscriptions completed")

        #if isSrAvailable:
        #    self.listen.setVocabulary(["start game", "start quiz"], False)
        #    self.listen.pause(False)

    def stop(self):
        #if self.memory_subscriber:
        #    self.memory_subscriber.signal.disconnect(self.on_face_detected)

        #self.talk_service.stop()
        self.talk_service = None
        #raise RuntimeError()

    def change_current_state(self, to_state):

        self.logger.verbose("Try acquire state change mutex")

        with self.state_lock:
            self.logger.verbose("Acquired state change mutex")
            self.game_state = to_state
            self.logger.verbose("State changed to {}".format(self.game_state))

        self.logger.verbose("Released state change mutex")

    def on_word_recognised(self, value):

        self.logger.info("Hit Word Recognised Callback")

        if self.game_state == STATE_IDLE and value[0] == "start game":

            self.start_game()

        #elif self.game_state == STATE_START_GAME:
        #    raise NotImplementedError()

        elif self.game_state == STATE_CONTINUE:
            raise NotImplementedError()

        elif self.game_state == STATE_PLAY_TRACK:
            raise NotImplementedError()

        #elif self.game_state == STATE_ASK_QUESTION:
        #    raise NotImplementedError()

        elif self.game_state == STATE_AWAIT_ANSWER:
            raise NotImplementedError()

        elif self.game_state == STATE_EVALUATE_ANSWER:

            self.evaluate_answer()

        #elif self.game_state == STATE_FEEDBACK_SUCCESS:
        #    raise NotImplementedError()

        #elif self.game_state == STATE_FEEDBACK_FAILURE:
        #    raise NotImplementedError()

        ##elif self.game_state == STATE_FEEDBACK_ENCOURAGEMENT:
        ##    raise NotImplementedError()

        ##elif self.game_state == STATE_FEEDBACK_TIMEOUT:
        ##    raise NotImplementedError()

    def start_game(self):

        self.change_current_state(STATE_CONTINUE)

        self.continue_round()

    def continue_round(self):

        self.change_current_state(STATE_CONTINUE)

        self.play_track()

    def play_track(self):

        # TODO: Capture these in game state
        title, artist = self.playlist_manager.playTrack()

        self.change_current_state(STATE_ASK_QUESTION)

        self.ask_question()

    def ask_question(self):

        question = random.randint(0, 1)
        if question == 0:
            self.talk_service.say("What's the name of this tune?")
        else:
            self.talk_service.say("Who sang this tune?")

        self.answer_timer = threading.Timer(10.0, self.give_feedback)
        self.answer_timer.start()

        self.change_current_state(STATE_AWAIT_ANSWER)

    def evaluate_answer(self):

        with self.feedback_lock:

            self.answer_timer.cancel()

            #TODO: This isn't quite right, but will do for now
            if self.game_state == STATE_FEEDBACK_ENCOURAGEMENT:

                self.talk_service.say("Oh no, time's up?")
                self.change_current_state(STATE_FEEDBACK_TIMEOUT)

            else:
                # TODO: This is incomplete
                # TODO: Get answer from somewhere and check against
                self.change_current_state(STATE_FEEDBACK_SUCCESS)

    def give_feedback(self):

        self.logger.verbose("Try acquire Mutex")
        with self.feedback_lock:
            self.logger.verbose("Mutex acquired")

            try:
                if self.game_state == STATE_AWAIT_ANSWER:
                    self.change_current_state(STATE_FEEDBACK_ENCOURAGEMENT)

                    self.talk_service.say("Time's almost up?")
                    self.answer_timer.cancel()
                    self.answer_timer = threading.Timer(5.0, self.evaluate_answer)
                    self.answer_timer.start()

            except:
                self.logger.fatal("Hopefully we never get here!")

        self.logger.verbose("Mutex released")


if __name__ == "__main__":

    try:
        connection_string = "--qi-url=tcp://"+ROBOT_IP+":"+ROBOT_PORT

        app = qi.Application([
            "QuizMaster",
            connection_string,
        ])
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