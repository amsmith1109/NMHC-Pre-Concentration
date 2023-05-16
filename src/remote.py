import signal
import sys
import time
import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

class remote():
    """
    remote is the object definition for the GPIO pins on the raspberry pi
    that connect to an HP5890 GC remote port. Each pin has a binary function 
    for simple communication between the GC and pre-concentration system:
    
    config - The pre-con tells the GC it is attached and to not accept
             manual triggers from the front panel.
    ready_in - GC indicates if it is ready to begin a run
    start_out - pre-concentration system tells the GC to begin a run
    start_in - the GC indicates that a run has started (usually not needed)
    ready - pre-con tells the GC it is ready (usually not needed)
    
    The GC output helps isolate itself from external electronics by using
    relay connections for its outputs. The "set" pins that are used
    are attached to one end of the corresponding relay on the GC, and the 
    input pins are attached to the other end of the relay.
    
    All connections use low-triggering
    """
    ############################################# 
    # Detection Events
    #############################################
    def ready_detected(self, pin):
        self.gc_ready = self.check_ready()

    def start_detected(self, pin):
        print('GC Run Started.')

    # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
    def __init__(self,
                 ready_in=27,   # Pin , 9
                 start_in=24,   # Pin , 8
                 set_ready=23,  # Pin , 5
                 set_start=25,  # Pin , 7
                 start=17,      # Pin , 1
                 ready=18,      # Pin , 12
                 config=22,     # Pin , 3
                 connected_obj=None):

        inPins = {'ready':ready_in, 'start': start_in}
        outPins = {'set ready': set_ready, 'set start': set_start,
                   'start': start, 'ready': ready, 'config': config}
        self.stime = time.time()
        ##### Store pin names & locations #####
        self.inPins = inPins
        self.outPins = outPins

        ##### Setup GPIO Input/Outputs #####
        GPIO.setmode(GPIO.BCM)
        for i in inPins.values():
            GPIO.setup(i, GPIO.IN)
        for i in outPins.values():
            GPIO.setup(i, GPIO.OUT, initial=1)

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
