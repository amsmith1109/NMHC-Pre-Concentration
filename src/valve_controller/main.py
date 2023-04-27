from machine import Pin
from multiport import multiport
import time
    
m = multiport()

##### Rotary Valve Setup #####
v = []
for i in [13, 12, 14, 27, 26, 25, 33, 32]:
    v.append(Pin(i, Pin.OUT, value=0))
    v[-1](0)
# Pin 13 = V0
# Pin 12 = V1
# Pin 14 = V2
# Pin 27 = V3
# Pin 26 = V4
# Pin 25 = V5
# Pin 33 = unused
# Pin 32 = vacuum pump

def pulse(pin=None, sleep=None):
    state = pin.value()
    pin(not(state))
    time.sleep(sleep)
    pin(state)
    print('ok')