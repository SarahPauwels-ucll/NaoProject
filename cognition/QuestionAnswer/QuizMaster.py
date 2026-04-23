import sys
import qi
import random
import Queue
import PlaylistManager
import PhysicalFeedback

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "52294"
#ROBOT_PORT = "9559"

proxies = [
    "ALTextToSpeech",
    "ALSpeechRecognition",
    "ALMemory",
    "ALLogger",
]

STATE_IDLE = "STATE_IDLE"
STATE_START_GAME = "STATE_START_GAME"
STATE_CONTINUE_GAME = "STATE_CONTINUE_GAME"
STATE_CONTINUE_ROUND = "STATE_CONTINUE_ROUND"
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

class QuizMaster:

    def __init__(self, app):

        self.app = app

        self.playlist_manager = None
        self.physical_feedback = None

        self.talk_service = self.app.session.service(proxies[0])
        self.listen = None
        self.isSrAvailable = False

        self.memory_service = self.app.session.service(proxies[2])
        self.memory_subscriber = None

        self.provider = None
        self.providerId = None
        self.logger = None

        self.register_logger()

        self.game_state = STATE_IDLE

        self.encourage_timer = None
        self.answer_timer = None

        self.current_question = None
        self.current_answer = None
        self.questions_asked = 0
        self.answered_right = 0
        self.questions_per_round = 2#5
        self.round_number = 0

        self.event_queue = Queue.Queue()
        self.worker_thread = None

    def register_logger(self):

        try:
            mod = qi.module("qicore")
            logmanager = app.session.service("LogManager")
            self.provider = mod.createObject("LogProvider", logmanager)
            self.providerId = logmanager.addProvider(self.provider)
        except RuntimeError:
            print "Defaulting to Virtual Robot Logging Mode"

        self.logger = qi.Logger("QuizMaster")

    def unregister_logger(self):

        if (self.providerId != None):
            mod = qi.module("qicore")
            logmanager = app.session.service("LogManager")
            logmanager.removeProvider(self.providerId)

    def set_asr_vocabulary(self, vocabulary):

        if self.isSrAvailable:
            self.listen.pause(True)
            self.listen.setVocabulary(vocabulary, False)
            self.listen.pause(False)

    def start(self):

        self.logger.info("QuizMaster Starting")

        self.start_playback_manager()
        self.start_word_recognition()

        self.logger.info("QuizMaster Started")

    def start_playback_manager(self):

        self.logger.info("Starting playback manager")

        self.playlist_manager = PlaylistManager.PlaylistManager(self.app, MUSIC_DIR)
        self.playlist_manager.initialisePlaylist()

        try:
            self.listen = app.session.service("ALSpeechRecognition")
            self.isSrAvailable = True
            self.set_asr_vocabulary(["start game", ])
        except:
            self.logger.error("Failed to get a handle to ALSpeechRecognition, defaulting to Virtual Robot Test Mode")
            print "Failed to get a handle to ALSpeechRecognition, defaulting to Virtual Robot Test Mode"

    def start_word_recognition(self):

        self.logger.info("Starting word recognition")

        #self.memory_subscriber.signal.connect(self.on_face_detected)
        self.memory_subscriber = self.memory_service.subscriber("WordRecognized")
        self.memory_subscriber.signal.connect(self.on_word_recognised)

        self.logger.info("QuizMaster subscriptions completed")

        self.worker_thread = qi.PeriodicTask()
        self.worker_thread.setCallback(self.run)
        self.worker_thread.setUsPeriod(1000000)
        self.worker_thread.start(True)

        self.logger.info("QuizMaster worker thread started")

    def run(self):

        try:
            event = self.event_queue.get(False)
            self._run_state_machine(event)
            self.event_queue.task_done()
        except Queue.Empty:
            pass

    def stop(self):
        #if self.memory_subscriber:
        #    self.memory_subscriber.signal.disconnect(self.on_face_detected)

        if self.isSrAvailable:
            self.talk_service.stop()
        self.talk_service = None

        self.unregister_logger()

    def change_current_state(self, to_state):

        self.game_state = to_state

    def on_word_recognised(self, value):

        self.logger.info("Hit Word Recognised Callback")

        self.event_queue.put(value)

    def _run_state_machine(self, value):

        self.logger.info("Run state machine")

        if self.game_state == STATE_IDLE and value is not None and value[0] == "start game" and value[1] > 0.4:
            self.change_current_state(STATE_START_GAME)
            self.event_queue.put(None)

        elif self.game_state == STATE_START_GAME:
            self.start_game()

        elif self.game_state == STATE_CONTINUE_GAME and value is not None:
            self.start_next_round(value)

        elif self.game_state == STATE_CONTINUE_ROUND:
            self.continue_round()

        elif self.game_state == STATE_PLAY_TRACK:
            self.play_track()

        elif self.game_state == STATE_ASK_QUESTION:
            self.ask_question()

        elif self.game_state == STATE_AWAIT_ANSWER and value is not None:
            self.evaluate_answer(value)

        elif self.game_state == STATE_FEEDBACK_SUCCESS:
            self.give_feedback()

        elif self.game_state == STATE_FEEDBACK_FAILURE:
            self.give_feedback()

        elif self.game_state == STATE_FEEDBACK_ENCOURAGEMENT:
            self.give_encouragement()

        elif self.game_state == STATE_FEEDBACK_TIMEOUT:
            self._answer_timeout()

        self.logger.info("State machine ran")

    def start_game(self):

        self.logger.info("Starting game")

        self.questions_asked = 0
        self.answered_right = 0

        self.round_number = 1
        self.talk_service.say("Round {}".format(self.round_number))

        self.change_current_state(STATE_CONTINUE_ROUND)
        self.event_queue.put(None)

    def start_next_round(self, isContinue):

        if isContinue[0] == "yes" and isContinue[1] > 0.4:
            self.answered_right = 0
            self.questions_asked = 0

            # TODO: Increase difficulty level
            self.round_number += 1
            self.talk_service.say("Round {}".format(self.round_number))

            self.change_current_state(STATE_CONTINUE_ROUND)
            self.event_queue.put(None)
        elif isContinue[0] == "no" and isContinue[1] > 0.4:
            self.talk_service.say("Oh, ok. See you next time!")
            self.set_asr_vocabulary(["start game", ])
            self.change_current_state(STATE_IDLE)
            self.event_queue.put(None)

    def continue_round(self):

        self.logger.info("Continuing round")

        self.encourage_timer = None
        self.answer_timer = None

        if self.questions_asked == self.questions_per_round:

            self.talk_service.say("Round complete, you scored {} out of {}".format(self.answered_right, self.questions_per_round))

            # TODO: Needs to ask if to play another round, but actually I think we another state.
            self.talk_service.say("Shall we play again?")
            self.set_asr_vocabulary(['yes', 'no' ])
            # TODO: We would need a timeout here

            self.change_current_state(STATE_CONTINUE_GAME)
            self.event_queue.put(None)
            return

        self.current_answer = None
        self.talk_service.say("Next question")
        self.change_current_state(STATE_ASK_QUESTION)
        self.event_queue.put(None)

    def play_track(self):

        self.logger.info("Playing track")

        # TODO: Capture these in game state
        title, artist = self.playlist_manager.playTrack()
        if self.current_question == 0:
            self.current_answer = title
        else:
            self.current_answer = artist
        self.logger.info(self.current_answer)

        self.set_asr_vocabulary([self.current_answer, ])

        self.change_current_state(STATE_AWAIT_ANSWER)
        self.event_queue.put(None)

        # self.encourage_timer = qi.async(self.prompt_for_encouragement, delay=10000000)
        # self.answer_timer = qi.async(self.prompt_answer_timeout, delay=15000000)

    def ask_question(self):

        self.logger.info("Asking question")

        self.current_question = random.randint(0, 1)
        if self.current_question == 0:
            self.talk_service.say("What's the name of this tune?")
        else:
            self.talk_service.say("Who sang this tune?")

        self.questions_asked += 1

        self.change_current_state(STATE_PLAY_TRACK)
        self.event_queue.put(None)

    def prompt_answer_timeout(self):

        self.logger.info("Prompt answer timeout")
        self.change_current_state(STATE_FEEDBACK_TIMEOUT)
        self.event_queue.put(None)

    def _answer_timeout(self):

        self.logger.info("Answer time up")

        #self.answer_timer = None
        self.talk_service.say("Oh no, time's up?")
        self.change_current_state(STATE_CONTINUE_ROUND)

        self.event_queue.put(None)

    def evaluate_answer(self, current_guess):

        self.logger.info("Evaluating answer")

        #self.cancel_timers()

        self.logger.info(current_guess)

        if self.current_answer == current_guess[0] and current_guess[1] > 0.4:
            self.change_current_state(STATE_FEEDBACK_SUCCESS)
            self.answered_right += 1
        else:

            self.change_current_state(STATE_FEEDBACK_FAILURE)

        self.event_queue.put(None)

    def cancel_timers(self):

        self.logger.info("Cancel timers")

        self.encourage_timer.cancel()
        if self.encourage_timer.isCanceled():
            self.logger.info("Encourage timer canceled")
        self.answer_timer.cancel()
        if self.answer_timer.isCanceled():
            self.logger.info("Answer timer canceled")

        if self.encourage_timer.isRunning():
            self.logger.info("Encourage timer running")
        if self.answer_timer.isRunning():
            self.logger.info("Answer timer running")

        self.encourage_timer = None
        self.answer_timer = None

    def prompt_for_encouragement(self):

        self.logger.info("Prompt encouragement")
        self.change_current_state(STATE_FEEDBACK_ENCOURAGEMENT)
        self.event_queue.put(None)

    def give_encouragement(self):

        self.logger.info("TBD2")

        self.talk_service.say("Time's almost up?")

        self.change_current_state(STATE_AWAIT_ANSWER)

    def give_feedback(self):

        self.logger.info("Giving feedback")

        if self.game_state == STATE_FEEDBACK_SUCCESS:
            self.talk_service.say("Well done, that's right!")
        else:
            self.talk_service.say("Better luck next time!")

        self.change_current_state(STATE_CONTINUE_ROUND)
        self.event_queue.put(None)

if __name__ == "__main__":

    try:
        connection_string = "--qi-url=tcp://"+ROBOT_IP+":"+ROBOT_PORT

        app = qi.Application([
            "QuizMaster",
            connection_string,
        ])
        app.start()

        quiz_master = QuizMaster(app)
        quiz_master.start()

        app.run()


    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)