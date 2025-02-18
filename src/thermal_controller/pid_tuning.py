from scipy.optimize import curve_fit
import numpy as np
import csv
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import time

''' Provides functionality for testing a PID controller

settings for the old 3S7P battery
p = 677, i = FFF, d = 0 
set_point = 350 yields stability at 275C with <10s ramp

Settings for new 20 Ah battery
p = 1F70
i and d didn't change the behavior at all
set_point = 550 yields stable temp of 290C w/ 5 s ramp 

Author - Alex Smith
email - alsmit2@pdx.edu
Last revised - 11/21/2023
'''


############################################################
# Setup
############################################################
def func(x, avg, mag, freq, phase):
    return avg + mag*np.cos(freq*x - phase)

def PID(x, T0, a0, a1, t0, t1, w, d):
    ''' function for describing the temperature change of a
    PID loop. Consists of two decaying exponentials.

    ramp is the rise from start to finish, is has the
    associated variables:
        - t0 is the time constant for ramp
        - a0 is the amplitude difference between initial and
            final temperatures

    ring is the overshoot oscillation and has the variables:
        - t1 is the time constant for ring
        - w (omega) is the frequency of oscillations during
            ringing
        - d (delta) is a phase offset for the cosine function

    T0 is the initial temperature

    x is the time variable
    '''
    ramp = a0*(1-np.exp(-x/t0))
    ring = a1*np.exp(-x/t1)*np.cos(w*x - d)
    return ramp + ring + T0

############################################################
# Take Measurements
############################################################
def run(ads, set_point=250, delay=20, plot=True):
    temp_ramp = [ads.measure()]
    t_ramp = [time.time()]
    ads.set_point(set_point)
    temp = [ads.measure()]
    t = [time.time()]
    while t[-1] < t[0] + delay:
        temp.append(ads.measure())
        t.append(time.time())

    ads.set_point(-99)
    try:
        while temp.index(False):
            idx = temp.index(False)
            del temp[idx]
            del t[idx]
    except ValueError:
        t = np.array(t) - t[0]
        temp = np.array(temp)

    if plot:
        plt.plot(t, temp, '*')
############################################################
# Curve Fitting
############################################################
    try:
        avg = sum(temp[-5:])/5
        g = (-5, avg, 50, 2, 10, 1, 0)
        popt = curve_fit(PID, t, temp, p0=g)

        xx = np.linspace(t[0], t[-1], 200)
        yy = PID(xx, *popt[0])

        if plot:
            plt.plot(xx, yy)
            plt.xlabel('[s]')
            deg = u'\N{DEGREE SIGN}'
            plt.ylabel(f'[{deg}C]')
    except RuntimeError:
        print('Fit failed.')
    if plot:
        plt.show()
    try:
        return round(popt[0][0] + popt[0][1], 1)
    except:
        return avg

def calibrate(pre_con, temp=None, delay=None):
    if temp is None:
        temp = [270, 290, 310]
    if delay is None:
        delay = 20
    pre_con.state('pre-backflush')
    pre_con.state('backflush')
    cooldown = {"name": "PID Calibration Cooldown",
                "ads": -27,
                "condition": "temp",
                "value": "<",
                "timeout": 10}
    stable = []
    for t in temp:
        pre_con.state(cooldown)
        stable.append(run(ads=pre_con.ads, set_point=t, delay=delay, plot=False))

    pre_con.state('off')
    print(stable)
    return np.polyfit(stable, temp, 1)
