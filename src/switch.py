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
                 pins = {'enable': 21,
                         'V0': 20,
                         'V1': 16,
                         'V2': 12,
                         'V3': 26,
                         'V4': 19,
                         'V5': 13,
                         'pump': 6},
                         print=1,
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
                                  bouncetime=50)
            self.state[self.keys[n]] = GPIO.input(i)
            
        signal.signal(signal.SIGINT, signal_handler)
        
if __name__ == '__main__':
    sw = switch()
    print('hello')