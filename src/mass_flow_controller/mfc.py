import time
import stats
from Calibration import calibration

class massFlowController:
    def __init__(self,
                 DAC=None,
                 ADC=None,
                 port = None,
                 units = None,
                 cal_file = None,
                 maxFlow = None,
                 timeout = 15):
        
        if DAC==None:
            print('No DAC provided.')
            return
        if ADC==None:
            print('No ADC provided.')
            return
        if port==None:
            print('Please specify the port used for the ADC/DAC.')
            return
        
        self.dac = DAC
        self.adc = ADC
        self.port = port
        self.timeout = timeout # in seconds
        if cal_file==None:
            self.cal = calibration()
        else:
            self.cal = calibration(cal_file = cal_file)                
        self.setpoint = 0
        if maxFlow == None:
            self.maxFlow = self.cal.invert(5)
        else:
            self.maxFlow = maxFlow
    
    def flowrate(self,
                 flow=None,
                 waiting=True,
                 display=False):
        if flow == None:
            voltage = self.adc.single(self.port)
            flow = self.cal.invert(voltage)
            if display:
                print('{} {}'.format(flow, self.cal.units))
            return flow
        else:
            if flow > self.maxFlow:
                flow = self.maxFlow
                print('Output capped at {} {}.'.format(flow, self.cal.units))
            voltage = self.cal.convert(flow)
            self.dac.write(self.port, voltage)
            self.setpoint = flow
            if flow == 0:
                self.dac.write(self.port, 0)
                print('MFC flow disabled.')
                return
            if waiting:
                count = 0
                time_stop = time.ticks_ms() + self.timeout*1000
                reading = []
                if flow < (.051 * self.maxFlow):
                    tolerance = .1
                else:
                    tolerance = .01
                while (time.ticks_ms() < time_stop):
                    reading.append(self.flowrate(display=False))
                    if display:
                        print(reading[-1])
                    error = abs((reading[-1] - flow)/flow)
                    accurate = error < tolerance
                    if len(reading) > 4:
                        std = stats.stdev(reading[-5:])
                        stable = std < tolerance*10
                    else:
                        stable = False
                    if accurate and stable:
                        count += 1
                    else:
                        count = 0
                    # The MFC is considered stable if it is <1% of the range
                    # after being polled 5 times in a row. This is to account
                    # for over/under-shoot. It will timeout if it does not reach
                    # stability within 5 seconds.
                    if count > 5:
                        timeout = (time.ticks_ms() - time_stop)/1000 + self.timeout
                        break
                    timeout = True
                    time.sleep(.1)
                if timeout==True:
                    print('Setpoint not reached before the timeout of {} s.'.format(self.timeout))
                    self.flowrate()
                else:
                    print('Setpoint of {} {} reached in {} s.'.format(flow, self.cal.units, timeout))
                

    #def autotune(self):
        