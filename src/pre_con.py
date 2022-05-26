from serial import Serial
from omega_tc import omegatc
from uPy import uPy

class Pre_con:
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
        
        vc = uPy(vc_port, baudrate=115200)
        mfc = uPy(mfc_port, baudrate=115200)
        ads_trap = omegatc(ads_trap_port)
        h20_trap = omegatc(h20_trap_port)
        
    def reset(self):
        for i in range(0,8):
            i
        
if __name__ == '__main__':
    print('testing pre_con')
    