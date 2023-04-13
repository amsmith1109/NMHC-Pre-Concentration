import time
import datetime
import csv
from src.thermal_controller.omega_tc import omegatc

o = omegatc('/dev/ttyUSB2')

d = []
t = [time.time()]
while time.time < t[0] + 3600:
    data.append(o.measure())
    t.append(time.time())
    print(d[-1])
    time.sleep(0.5)
    
name = str(datetime.datetime.today())
idx = name.find('.')
name = name[:idx]
with open('{} temp test.csv'.format(name)) as f:
    writer = csv.writer(f)
    writer.writerows(zip(t, d))