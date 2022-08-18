from machine import Pin
from multiport import multiport
import time

def name():
    print('Valve Controller - Ver. 0.1')
    
m = multiport()

##### Rotary Valve Setup #####
lst = [13, 12, 14, 27, 26, 25, 33, 32]
v = []
for i in lst:
    v.append(Pin(i, Pin.OUT))
    v[-1](0)