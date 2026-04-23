import qi
import time
import math


CELEBRATE_JOINTS = [
    "LShoulderRoll",
    "LShoulderPitch",
    "RShoulderRoll",
    "RShoulderPitch",
    "LElbowRoll",
    "LElbowYaw",
    "LHand",
    "RElbowRoll",
    "RElbowYaw",
    "RHand",
]

half = math.pi/2
quarter = math.pi/4
eighth = math.pi/8

CELEBRATE_ANGLES = [
    [
        quarter,
        -eighth,
        -quarter,
        -eighth,
        0,0,0,0,0,0,
    ],
    [
        0,0,0,0,
        -half,
        -half,
        0,
        half,
        half,
        0,
    ],
]

COMMISTERATE_JOINTS = [
    "LElbowRoll",
    "LElbowYaw",
    "LWristYaw",
    "LHand",
    "RElbowRoll",
    "RElbowYaw",
    "RWristYaw",
    "RHand",
]

COMMISTERATE_ANGLES = [
    -half,
    -half,
    -half,
    1,
    half,
    half,
    half,
    1,
]

class PhysicalFeedback:

    def __init__(self, app):

        self.app = app
        self.move = self.app.session.service("ALMotion")
        self.pose = self.app.session.service("ALRobotPosture")

        if not self.move.robotIsWakeUp():
            self.move.wakeUp()

    def celebrate(self):

        times = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        isAbsolute = True

        self.move.angleInterpolation(CELEBRATE_JOINTS, CELEBRATE_ANGLES[1], times, isAbsolute, _async=True)

    def commiserate(self):

        times = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        isAbsolute = True
        self.move.angleInterpolation(COMMISTERATE_JOINTS, COMMISTERATE_ANGLES, times, isAbsolute, _async=True)

    def hurry(self):
        pass