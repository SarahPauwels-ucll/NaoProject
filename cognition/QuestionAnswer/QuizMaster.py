import sys
import qi
import random
import Queue
import PlaylistManager

ROBOT_IP = "127.0.0.1"
#ROBOT_PORT = "64286"
#ROBOT_IP = "172.18.16.47"
ROBOT_PORT = "9559"

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

MUSIC_DIR = "/home/nao/music"
#MUSIC_DIR = "C:/GitRepos/ENG7007_PRAC1_GROUP/NaoProject/cognition/music_quiz/music"

class QuizMaster:

    def __init__(self, app, talk, listen, remember):

        self.app = app

        self.playlist_manager = None

        self.talk_service = talk
        self.listen = listen

        self.memory_service = remember
        self.memory_subscriber = None

        mod = qi.module("qicore")
        logmanager = app.session.service("LogManager")
        self.provider = mod.createObject("LogProvider", logmanager)
        self.providerId = logmanager.addProvider(self.provider)
        #self.logger = qi.Logger("QuizMaster")
        self.logger = qi.Logger("QuizMaster")

        self.game_state = STATE_IDLE

        self.encourage_timer = None
        self.answer_timer = None

        self.current_question = None
        self.current_answer = None
        self.questions_asked = 0
        self.answered_right = 0
        self.questions_per_round = 2#5

        self.event_queue = Queue.Queue()
        self.worker_thread = None

    def start(self):

        self.logger.info("QuizMaster Starting")

        self.playlist_manager = PlaylistManager.PlaylistManager(self.app, MUSIC_DIR)
        self.playlist_manager.initialisePlaylist()

        isSrAvailable = True
        try:
            self.listen = app.session.service("ALSpeechRecognition")
            self.listen.pause(True)
        except:
            self.logger.error("Failed to get a handle to ALSpeechRecognition, defaulting to Virtual Robot Test Mode")
            print "Failed to get a handle to ALSpeechRecognition, defaulting to Virtual Robot Test Mode"
            isSrAvailable = False

        #self.memory_subscriber.signal.connect(self.on_face_detected)
        self.memory_subscriber = self.memory_service.subscriber("WordRecognized")
        self.memory_subscriber.signal.connect(self.on_word_recognised)

        self.logger.info("QuizMaster subscriptions completed")

        #self.worker_thread.start()
        self.worker_thread = qi.PeriodicTask()
        self.worker_thread.setCallback(self.run)
        self.worker_thread.setUsPeriod(1000000)
        self.worker_thread.start(True)

        self.logger.info("QuizMaster worker thread started")

        #if isSrAvailable:
        #    self.listen.setVocabulary(["start game", "start quiz"], False)
        #    self.listen.pause(False)

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

        #self.talk_service.stop()
        self.talk_service = None
        #raise RuntimeError()

    def change_current_state(self, to_state):

        self.game_state = to_state

    def on_word_recognised(self, value):

        self.logger.info("Hit Word Recognised Callback")

        self.event_queue.put(value)

    def _run_state_machine(self, value):

        self.logger.info("Run state machine")

        if self.game_state == STATE_IDLE and value[0] == "start game":
            self.change_current_state(STATE_START_GAME)
            self.event_queue.put(None)

        elif self.game_state == STATE_START_GAME:
            self.start_game()

        elif self.game_state == STATE_CONTINUE:
            self.continue_round()

        elif self.game_state == STATE_PLAY_TRACK:
            self.play_track()

        elif self.game_state == STATE_ASK_QUESTION:
            self.ask_question()

        elif self.game_state == STATE_AWAIT_ANSWER and value is not None:
            self.evaluate_answer(value[0])

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

        self.change_current_state(STATE_CONTINUE)

        self.questions_asked = 0
        self.answered_right = 0

        self.change_current_state(STATE_CONTINUE)
        self.event_queue.put(None)

    def continue_round(self):

        self.logger.info("Continuing round")

        self.encourage_timer = None
        self.answer_timer = None

        if self.questions_asked == self.questions_per_round:
           self.talk_service.say("Round complete, you scored {} out of {}".format(self.answered_right, self.questions_per_round))
           sys.exit(0)

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
        self.change_current_state(STATE_CONTINUE)

        self.event_queue.put(None)

    def evaluate_answer(self, current_guess):

        self.logger.info("Evaluating answer")

        #self.cancel_timers()

        self.logger.info(current_guess)

        if self.current_answer == current_guess:
            self.change_current_state(STATE_FEEDBACK_SUCCESS)
            self.answered_right += 1
        else:

            self.change_current_state(STATE_FEEDBACK_FAILURE)

        #self.give_feedback()
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

        self.change_current_state(STATE_CONTINUE)
        self.event_queue.put(None)

if __name__ == "__main__":

    try:
        connection_string = "--qi-url=tcp://"+ROBOT_IP+":"+ROBOT_PORT

        app = qi.Application([
            "QuizMaster",
            connection_string,
        ])
        app.start()

        talk = app.session.service(proxies[0])
        listen = app.session.service(proxies[1])
        remember = app.session.service(proxies[2])

        quiz_master = QuizMaster(app, talk, listen, remember)
        quiz_master.start()

        app.run()


    except RuntimeError as ex:
        print(ex)
        sys.exit(-1)