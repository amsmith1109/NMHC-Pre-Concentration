import time

class massFlowController:
    def __init__(self,
                 DAC=None,
                 ADC=None,
                 maxFlow = None,
                 port = None,
                 units = 'ccpm',
                 input_range = None,
                 output_range = None,
                 timeout = 5):
        
        if DAC==None:
            print('No DAC provided.')
        if ADC==None:
            print('No ADC provided.')
        if port==None:
            print('Please specify a port.')
        
        self.dac = DAC
        self.adc = ADC
        self.maxFlow = maxFlow
        self.units = units
        self.port = port
        self.timeout = timeout #Note that these are in seconds
        if maxFlow!=None:
            if (input_range==None) & (output_range==None):
                self.cal = linear_calibration([0, maxFlow], [0.2, 5])
            else:
                self.cal = linear_calibration(input_range, output_range)                
        self.setpoint = 0
    
    def flowrate(self, flow, waiting=None):
        if flow > self.maxFlow:
            flow = self.maxFlow
            print('Output capped at {} {}.'.format(flow, self.units))
        voltage = self.cal.convert(flow)
        self.dac.write(self.port, voltage)
        self.setpoint = flow
        timeout = 0
        if waiting:
            count = 0
            time_stop = time.time() + self.timeout
            while (time.time() < time_stop):
                reading = self.check()
                if abs(reading - flow)/flow < 0.01:
                    count += 1
                else:
                    count = 0
                # The MFC is considered stable if it is <1% of the range
                # after being polled 5 times in a row. This is to account
                # for over/under-shoot.
                if count > 5:
                    timeout = time.time() - t_stop + self.timeout
                    break
                timeout = True
                time.sleep(.1)
            if timeout==True:
                print('Setpoint not reached before the timeout of {} s.'.format(self.timeout))
            else:
                print('Setpoint reached in {} s.'.format(timeout))
        return
    
    def check(self):
        voltage = self.adc.single(self.port)
        flow = self.cal.invert(voltage)
        return flow
    
class linear_calibration:
    def __init__(self,
                 input_range,
                 output_range):
        self.calibrate(input_range, output_range)
    
    # return y from y = mx + b (x is provided)
    def convert(self, x):
        y = x*self.scale + self.offset
        return y
    
    # Return x from y = mx + b (y is provided)
    def invert(self, y):
        x = (y - self.offset)/self.scale
        return x
    
    # Perform a regression on a set of inputs to obtain
    # the offset and scale parameters.
    # Using this instead of importing a library to save space.
    def calibrate(self, flow_rate, voltage):
        count = len(flow_rate)
        if count != len(voltage):
            print('Inputs must be the same size!')
            return
        sum_y = sum(voltage)
        sum_x = sum(flow_rate)
        sum_x2 = sum([i**2 for i in flow_rate])
        sum_xy = sum([i*j for i,j in zip(flow_rate, voltage)])        
        _delta = count*sum_x2 - sum_x**2
        scale = (count*sum_xy - sum_x*sum_y)/_delta
        offset = (sum_y*sum_x2 - sum_x*sum_xy)/_delta
        
        self.scale = scale
        self.offset = offset
