from scipy.optimize import curve_fit as cf
import numpy as np
import csv
import matplotlib.pyplot as plt

folder = ''
fname = 'tempdata19.csv'
file = folder + fname
data = []
with open(file, 'r') as f:
    raw_data = csv.reader(f)
    for rows in raw_data:
        data.append(rows)

t = []
temp = []
for x in data[0]:
    t.append(float(x))

for x in data[1]:
    temp.append(float(x))


def func(x, avg, mag, freq, phase):
    return avg + mag*np.cos(freq*x - phase)


def guess(xData, yData):
    avg = np.average(yData)
    mag = (np.max(yData) + np.min(yData) - avg)/2
    dx = np.diff(yData) > 1
    first = dx.tolist().index(True)
    dx = dx[first:]
    second = dx.tolist().index(False)
    dx = dx[second:]
    DX = dx.tolist().index(True)
    tau = xData[DX + second] - xData[second]
    freq = np.pi/tau
    phase = (second/DX - .5) * np.pi
    return avg, mag, freq, phase

try:
    g = guess(t, temp)
except:
    g = (140, 0, .7, 1)

t = np.array(t)
avg = np.average(temp)
avg = 0
temp = np.array(temp) - avg

popt = cf(func, t, temp, p0=g)

print(f'avg = {popt[0][0]}')
print(f'mag = {abs(popt[0][1])}')
print(f'freq = {popt[0][2]}')

xx = np.linspace(t[0], t[-1], 200)
yy = func(xx, *popt[0])
plt.plot(t, temp, '*')
plt.plot(xx, yy)
plt.show()
