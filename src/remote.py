import signal
import sys
import time
import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class remote():
    ##### Detection Events #####
    def ready_detected(self, pin):
        self.gc_ready = self.check_ready()
#         if self.ready:
#             print('GC ready.')
        
    
    def start_detected(self, pin):
        print('GC Run Started.')
        
    def __init__(self,
             # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
             inPins =  {'ready':    27,      # Pin , 9
                        'start':    24},     # Pin , 8
             outPins = {'set ready':23,  # Pin , 5
                        'set start':25,  # Pin , 7
                        'start':    17,      # Pin , 1
                        'ready':    18,      # Pin , 12
                        'config':   22},    # Pin , 3
                         connected_obj=None):
        
        self.stime = time.time()
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
                              GPIO.BOTH,
                              callback=self.ready_detected,
                              bouncetime=100)
        GPIO.add_event_detect(inPins['start'],
                              GPIO.BOTH,
                              callback=self.start_detected,
                              bouncetime=45)
        self.gc_ready = self.check_ready()
        self.config(0)
        signal.signal(signal.SIGINT, signal_handler)
    
    ##### Configure output functions #####
    def start(self):
        GPIO.output(self.outPins['start'], 0)
        time.sleep(.06)
        GPIO.output(self.outPins['start'], 1)
    
    def ready(self, val=1):
        GPIO.output(self.outPins['ready'], val)
        
    def config(self, val=1):
        GPIO.output(self.outPins['config'], val)
    
    def check_ready(self):
        return not GPIO.input(self.inPins['ready'])
    
if __name__ == '__main__':
    rm = remote()
        