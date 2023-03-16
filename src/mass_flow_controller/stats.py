import math

def stdev(x):
    var = variance(x)
    return math.sqrt(var)
    
def variance(data):
    avg, n = mean(data)
    deviations = [(x - avg) ** 2 for x in data]
    variance = sum(deviations) / (n - 1)
    return variance
    
def mean(x):
    n = len(x)
    return sum(x)/n, n
