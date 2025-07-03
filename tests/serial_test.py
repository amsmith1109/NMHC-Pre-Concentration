import serial
import threading
import time

if __name__ == '__main__':
    s = serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=.2)
    for i in range(1000
                   ):
        msg = 'dir()'.encode('utf-8')
        s.write(msg + b'\r')
        print(s.readall())
        time.sleep(.01)
    s.close()
