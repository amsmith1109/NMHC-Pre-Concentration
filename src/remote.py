import signal
import sys

import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class remote():
    def __init__(self,
             # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
             inPins =  {'ready NO':25,  # Pin 22, 9
                        'start A':24},  # Pin 18, 8}
             outPins = {'ready C':22,   # Pin 15, 5
                        'start B':23,   # Pin 16, 7
                        'start':17,     # Pin 11, 1
                        'ready':18,     # Pin 12, 12
                        'config':27}):  # Pin 13, 3
        self.inPins = inPins
        self.outPins = outPins
        GPIO.setmode(GPIO.BCM)
        