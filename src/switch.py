import signal
import sys

import RPi.GPIO as GPIO

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
    
class switch:
    def switch_detected(self, channel):
        idx = self.pin_list.index(channel)
        name = self.keys[idx]
        new_value = GPIO.input(channel)
        self.state[name] = new_value
        if self.connected_obj != None:
            self.connected_obj.switch_state = self.state
    
    def __init__(self,
                 pins = {'enable': 6,   # Pin 31
                         'V0': 13,      # Pin 33
                         'V1': 19,      # Pin 35
                         'V2': 26,      # Pin 37
                         'V3': 12,      # Pin 32
                         'V4': 16,      # Pin 36
                         'V5': 20,      # Pin 38
                         'pump': 21},   # Pin 40
                         connected_obj=None):                 
        self.pins = pins
        self.keys = [x for x in pins.keys()]
        self.pin_list = [x for x in pins.values()]
        self.state = {}
        self.connected_obj = connected_obj
        
        GPIO.setmode(GPIO.BCM)
        keys = self.pins.keys()
        for n, i in enumerate(self.pin_list):
            GPIO.setup(i, GPIO.IN)
            GPIO.add_event_detect(i,
                                  GPIO.BOTH,
                                  callback=self.switch_detected,
                                  bouncetime=10)
            self.state[self.keys[n]] = GPIO.input(i)
            
        signal.signal(signal.SIGINT, signal_handler)
        
if __name__ == '__main__':
    sw = switch()
