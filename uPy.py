from serial import Serial
import time

class uPy:
    def __init__(self,
                 port):
        self.serial = Serial(port, baudrate=115200, timeout=0.05)
        
    def write(self, msg):
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message).encode('utf-8')
        else:
            print('Invalid input variable type.')
        
        if msg[-1] != b'\r': 
            msg = msg + b'\r'
            
        self.serial.write(msg)
        
    def read(self):
        msg = self.serial.readall()
        msg = msg.decode("utf-8")
        return msg
    
    def echo(self, msg):
        self.write(msg)
        message = self.read()
        return message