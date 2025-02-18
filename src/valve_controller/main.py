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

def rotate(position=None, valve=None):
    if isinstance(valve, (float, int, range, list)):
        if isinstance(position, (float, int, range, list)):
            if len(valve) != len(position):
                raise ValueError('Pin and position specifications need to be the same length.')
    if valve == None:
        if position==None:
            for i in v:
                print(i.value())
            return
        else:
            if len(position) != 6:
                raise ValueError('Position must be a list the position of all 6 valves.')
            for index, value in enumerate(position):
                v[index](value)
    else:
        v[valve](position)

def pulse(pin=None, sleep=None):
    state = pin.value()
    pin(not(state))
    time.sleep(sleep)
    pin(state)
    print('ok')