from serial import Serial
from thermal_controller.omega_tc import omegatc
from uPy import uPy

class pre_con:
    def __init__(self,
                 vc_port = '/dev/ttyACM0',
                 mfc_port = '/dev/ttyUSB2',
                 ads_trap_port = '/dev/ttyUSB0',
                 h20_trap_port = '/dev/ttyUSB1'):
        
        # It is very important that the USB configuration matches the usb ports
        # Improvements should be made to automatically determine where each
        # device is actually located. The ESP32 & ESP8266 can easily be programmed
        # to respond some form of identifier
        self.vc_port = vc_port
        self.mfc_port = mfc_port
        self.ads_trap_port = ads_trap_port
        self.h20_trap_port = h20_trap_port
        
        self.vc = uPy(vc_port)
        self.mfc = uPy(mfc_port)
        #self.ads_trap = omegatc(ads_trap_port)
        #self.h20_trap = omegatc(h20_trap_port)
        
    def valve(self, V, position):
        if isinstance(V, int):
            self.vc.write(f'v[{V}]({position})')
        elif isinstance(V, list) or isinstance(V, range):
            for n, i in enumerate(V):
                if isinstance(position, int):
                    self.vc.write(f'v[{i}]({position})')
                else:
                    self.vc.write(f'v[{i}]({position[n]})')
        
if __name__ == '__main__':
    pc = pre_con()
    pc.valve(range(0,8),1)