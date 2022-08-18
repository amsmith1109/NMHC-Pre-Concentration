from serial import Serial
from thermal_controller.omega_tc import omegatc
from uPy import uPy

class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB2',
                 ads_trap_port = '/dev/ttyUSB0',
                 h2o_trap_port = '/dev/ttyUSB1'):
        
        # It is very important that the USB configuration matches the usb ports
        # Improvements should be made to automatically determine where each
        # device is actually located. The ESP32 & ESP8266 can easily be programmed
        # to respond some form of identifier
        self.vc_port = vc_port
        self.mfc_port = mfc_port
        self.ads_trap_port = ads_trap_port
        self.h2o_trap_port = h2o_trap_port
        
        self.vc = uPy(vc_port)
        self.mfc = uPy(mfc_port)
        #self.ads_trap = omegatc(ads_trap_port)
        #self.h2o_trap = omegatc(h2o_trap_port)
        
    def valve(self, V, position):
        if isinstance(V, int):
            self.vc.write(f'v[{V}]({position})\r')
        elif isinstance(V, list) or isinstance(V, range):
            for n, i in enumerate(V):
                if isinstance(position, int):
                    self.vc.write(f'v[{i}]({position})\r')
                else:
                    self.vc.write(f'v[{i}]({position[n]})\r')
        
    def home_valves(self):
        self.valve(range(0,8),0)
        
if __name__ == '__main__':
    pc = pre_con()
    #pc.valve(range(0,8),1)
    #ads = pc.h2o_trap
    v = pc.vc
    
    ## Rotate valves
    
    # Perform a rotation individually
    #pc.valve(0,0)
    
    # Or do them all at once by passing a list or range
    #pc.valve([1,2],0)
    #pc.valve(range(3,8),0)
    
    # There is also a built in macro to home all of them
    # This is equivalent to .valve(range(0,8),0)
    #pc.home_valves()