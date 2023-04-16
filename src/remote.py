import signal
import sys

import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class remote():
    ##### Detection Events #####
    def ready_detected(self):
        print('Ready signal detected.')
    
    def start_detected(self):
        print('Start signal detected.')
        
    
    def __init__(self,
             # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
             inPins =  {'ready':25,      # Pin 22, 9
                        'start':24},     # Pin 18, 8}
             outPins = {'set ready':22,  # Pin 15, 5
                        'set start':23,  # Pin 16, 7
                        'start':17,      # Pin 11, 1
                        'ready':18,      # Pin 12, 12
                        'config':27},    # Pin 13, 3
                         connected_obj=None):
        
        ##### Store pin names & locations #####      
        self.inPins =  inPins
        self.outPins = outPins
        
        ##### Setup GPIO Input/Outputs #####
        GPIO.setmode(GPIO.BCM)
        for i in inPins.values():
            GPIO.setup(i, GPIO.IN)
        for i in outPins.values():
            GPIO.setup(i, GPIO.OUT, initial=1)
        """
        The "set" pins are attached to a relay on the GC.
        The two input pins will detect a normal high, so the set
        pins are set to ground to signal when a contact closue occurs.
        """
        GPIO.output(outPins['set start'], 0)
        GPIO.output(outPins['set ready'], 0)
        
        ##### Configure input detection events #####
        GPIO.add_event_detect(inPins['ready'],
                              GPIO.FALLING,
                              callback=self.ready_detected,
                              bouncetime=1)
        GPIO.add_event_detect(inPins['start'],
                              GPIO.FALLING,
                              callback=self.start_detected,
                              bouncetime=1)

        signal.signal(signal.SIGINT, signal_handler)
    
    ##### Configure output functions #####
    def start(self):
        GPIO.output(self.outPins['start'],0)
    
    def ready(self):
        GPIO.output(self.outPins['ready'],0)
        
    def config(self):
        GPIO.output(self.outPins['config'],0)
    
if __name__ == '__main__':
    rm = remote()