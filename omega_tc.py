import serial
import time

class omegatc:
    def __init__(self,
                 com,
                 baud=9600,
                 parity=serial.PARITY_ODD,
                 stops=serial.STOPBITS_ONE,
                 size=serial.SEVENBITS,
                 timeout=0.05,
                 recognition='*',
                 Addr=1):
        
        self.serial = serial.Serial(
            com,
            baudrate=baud,
            parity=parity,
            stopbits=stops,
            bytesize=size,
            timeout=timeout)
        
        self.recognition = recognition
        self.port = com
        self.address = Addr
            
    def model(self):
        self.serial.write(b'ENQ')
        txt = serlf.serial.readall()
        print(txt)
        
    def write(self, message):
        #Check input type and convert it to byte string
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message)
            msg = msg.encode('utf-8')
        else:
            print('Incorrect message')
            
        self.serial.write(msg)
        
    def read(self):
        print(self.serial.readall())
        
    def readline(self):
        print(self.serial.readline())
        
    def close(self):
        self.serial.close()
        
    def rc(self, message):
        self.write(message)
        time.sleep(0.5)
        self.read()