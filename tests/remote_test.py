import signal
import sys

import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class remote():
    def signal_detected(self, pin):
        idx = list(self.pins.values()).index(pin)
        name = list(self.pins.keys())[idx]
        print('{} signal detected.'.format(name))
        print(pin)
        
    def __init__(self,
             # Declared pin = RPi GPIO, Pin comments are "RPi Pin #, HP5890 Pin #"
             pins =    {'read ready':27, # Pin , 9
                        'read start':24, # Pin , 8
                        'set ready':23,  # Pin , 5
                        'set start':25,  # Pin , 7
                        'start':17,      # Pin , 1
                        'ready':18,      # Pin , 12
                        'config':22},    # Pin , 3
                      connected_obj=None):
        self.pins = pins
        GPIO.setmode(GPIO.BCM)
        for i in pins.values():
            GPIO.setup(i, GPIO.IN)
            GPIO.add_event_detect(i,
                              GPIO.FALLING,
                              callback=self.signal_detected,
                              bouncetime=100)

        signal.signal(signal.SIGINT, signal_handler)
    
if __name__ == '__main__':
    rm = remote()
        