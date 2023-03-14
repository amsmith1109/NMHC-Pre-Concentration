import time
from Calibration import calibration

class massFlowController:
    def __init__(self,
                 DAC=None,
                 ADC=None,
                 port = None,
                 units = None,
                 cal_file = None,
                 timeout = 5):
        
        if DAC==None:
            print('No DAC provided.')
        if ADC==None:
            print('No ADC provided.')
        if port==None:
            print('Please specify the port used for the ADC/DAC.')
        
        self.dac = DAC
        self.adc = ADC
        self.port = port
        self.timeout = timeout #Note that these are in seconds
        if cal_file==None:
            self.cal = calibration()
        else:
            self.cal = calibration(cal_file = cal_file)                
        self.setpoint = 0
        self.maxFlow = self.cal.invert(5)
    
    def flowrate(self,
                 flow=None,
                 waiting=None):
        if flow == None:
            voltage = self.adc.single(self.port)
            flow = self.cal.invert(voltage)
            print('{} {}'.format(flow, self.cal.units))
            return flow
        else:
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
                    # for over/under-shoot. It will timeout if it does not reach
                    # stability within 5 seconds.
                    if count > 5:
                        timeout = time.time() - t_stop + self.timeout
                        break
                    timeout = True
                    time.sleep(.1)
                if timeout==True:
                    print('Setpoint not reached before the timeout of {} s.'.format(self.timeout))
                else:
                    print('Setpoint of {} {} reached in {} s.'.format(flow, self.cal.units, time))
    
