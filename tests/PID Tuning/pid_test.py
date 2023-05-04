from scipy.optimize import curve_fit as cf
import numpy as np
import csv
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# last good settings
# p = 677, i = FFF, d = 0
# where set_point = 350
# yielded stability at 275C with <10s ramp

############################################################
# Setup
############################################################
def func(x, avg, mag, freq, phase):
    return avg + mag*np.cos(freq*x - phase)

def guess(xData, yData):
    avg = np.average(yData)
    mag = (np.max(yData) + np.min(yData) - avg)/2
    dx = np.diff(yData) > 1
    try:
        first = dx.tolist().index(True)
        dx = dx[first:]
        second = dx.tolist().index(False)
        dx = dx[second:]
        DX = dx.tolist().index(True)
        tau = xData[DX + second] - xData[second]
        freq = np.pi/tau
    except:
        freq = 1
    phase = (second/DX - .5) * np.pi
    return avg, mag, freq, phase

############################################################
# Take Measurements
############################################################
def run(set_point=200, delay=60):
    temp_ramp = [pc.ads.measure()]
    t_ramp = [time.time()]
    pc.ads.set_point(set_point)
    # while temp_ramp[-1] < set_point:
    #     temp_ramp.append(pc.ads.measure())
    #     t_ramp.append(time.time())
    #     time.sleep(.01)
    #     if time.time() > (t_ramp[0] + 30):
    #         break
    # print(round(t_ramp[-1] - t_ramp[0],1))
    temp = [pc.ads.measure()]
    t = [time.time()]
    while t[-1] < t[0] + delay:
        temp.append(pc.ads.measure())
        t.append(time.time())
        
    pc.ads.set_point(-99)
    try:
        while temp.index(False):
            idx = temp.index(False)
            del temp[idx]
            del t[idx]
    except ValueError:
        t = np.array(t) - t[0]
        temp = np.array(temp)
        
    plt.plot(t, temp, '*')
############################################################
# Curve Fitting
############################################################
    # g = guess(t, temp)
    try:
        g = (set_point, 100, 1, 0)
        popt = cf(func, t, temp, p0=g)

        print(f'avg = {popt[0][0]}')
        print(f'mag = {abs(popt[0][1])}')
        print(f'freq = {popt[0][2]}')

        xx = np.linspace(t[0], t[-1], 200)
        yy = func(xx, *popt[0])

        plt.plot(xx, yy)
    except RuntimeError:
        print('Fit failed.')
    plt.show()
    return t, temp, popt



############################################################
# Code for saving Data
############################################################
# fname = datetime.today().strftime('%Y-%m-%d - %H;%M')
# fname += '.cvs'
# with open(fname, 'w') as f:
#     file = csv.writer(f)
#     file.writerows(data)
