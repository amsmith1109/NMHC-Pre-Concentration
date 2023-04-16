import signal
import sys

import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class remote():
    def __init__(self,
             # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
             inPins =  {'ready':25,  # Pin 22, 9
                        'start':24},  # Pin 18, 8}
             outPins = {'ready':22,   # Pin 15, 5
                        'set start':23,   # Pin 16, 7
                        'start':17,     # Pin 11, 1
                        'set ready':18,     # Pin 12, 12
                        'config':27}):  # Pin 13, 3

        GPIO.setmode(GPIO.BCM)
        
        self.inKeys =  [x for x in inPins.keys()]
        self.inPins =  [x for x in inPins.values()]
        self.outKeys = [x for x in outPins.keys()]
        self.outPins = [x for x in outPins.values()]
        for i in self.inPins:
            GPIO.setup(i, GPIO.IN)
        for i in self.outPins:
            GPIO.setup(i, GPIO.OUT, initial=0)
        
    def check_ready(self):
        pin = self.inPins['ready']
        return GPIO.input(pin)
    
if __name__ == '__main__':
    rm = remote()