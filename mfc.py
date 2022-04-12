class mfc:
    def __init__(self,
                 DAC,
                 ADC,
                 maxFlow = 50,
                 units = 'ccpm',
                 offset = 0,
                 scale = 1)
    
        self.dac = DAC
        self.adc = ADC
        self.maxFlow = maxFlow
        self.units = units
        self.cal.offset = offset
        self.cal.scale = scale
        
    
    def flow2voltage(self, flow):
        
        return
    
class linear_calibration:
    def __init__(self,
                 offset = 0,
                 scale = 1)
        self.offset = offset
        self.scale = scale
    
    # return y from y = mx + b (x is provided)
    def convert(self, val):
        return val*self.scale + self.offset
    
    # Return x from y = mx + b (y is provided)
    def invert(self, val):
        return (val - self.offset)/self.scale
    
    # Perform a regression on a set of inputs to obtain
    # the offset and scale parameters.
    # Using this instead of importing a library to save space.
    def calibrate(self, x, y):
        count = len(x)
        if count != len(y):
            print('Inputs must be the same size!')
            return
        sum_y = sum(y)
        sum_x = sum(x)
        sum_x2 = sum([i**2 for i in x])
        sum_xy = sum([i*j for i,j in zip(x,y)])        
        _delta = coun*sum_x2 - sum_x**2
        scale = (count*sum_xy - sum_x*sum_y)/_delta
        offset = (sum_y*sum_x2 - sum_x*sum_xy)/_delta
        
        self.scale = scale
        self.offset = offset
        