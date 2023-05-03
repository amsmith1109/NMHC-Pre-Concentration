import csv
fname = 'tempdata14.csv'

set_point = 200

temp_ramp = [pc.ads.measure()]
t_ramp = [time.time()]
pc.ads.set_point(200)
while temp_ramp[-1] < set_point:
    temp_ramp.append(pc.ads.measure())
    t_ramp.append(time.time())
    time.sleep(.01)
    if time.time() > (t_ramp[0] + 30):
        break
print(round(t_ramp[-1] - t_ramp[0],1))
temp = [pc.ads.measure()]
t = [time.time()]
while t[-1] < t[0] + 30:
    temp.append(pc.ads.measure())
    t.append(time.time())
    
t = [x-t[0] for x in t]
pc.ads.set_point(-99)

data = [t, temp]
with open(fname, 'w') as f:
    file = csv.writer(f)
    file.writerows(data)

# pc.ads.set_point(200, eeprom=1)