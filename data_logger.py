from omega_tc import omegatc
from serial_port import serial_ports
import time
import numpy as np
from datetime import datetime

s = serial_ports()
o = omegatc(s[0])

d = []
t = []
dt = datetime.now()
t0 = time.time()
while time.time() < (t0 + 900):
    d.append(o.measure())
    t.append(time.time())
    print(d[-1])
    time.sleep(.25)
    
data = []
rt = []
for n, i in enumerate(d):
                    if i!=None:
                        data.append(i)
                        rt.append(t[n])
                        
txt = 'Datalog - %s.csv'%dt.strftime('%d-%m-%Y, %H:%M:%S')
np.savetxt(txt, np.vstack((rt,data)).T, delimiter=', ')