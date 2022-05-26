from serial import Serial
import time

class uPy:
    def __init__(self,
                 port,
                 baudrate=115200,
                 timeout=0.05):
        self.serial = Serial(port, baudrate=115200, timeout=0.05)
        
    def write(self, message):
        # convert input to byte string
        if isinstance(message, str):
            msg = message.encode('utf-8')
        elif isinstance(message, bytes):
            msg = message
        elif isinstance(message, float) or isinstance(message, int):
            msg = str(message).encode('utf-8')
        else:
            print('Invalid input variable type.')
        
        # add carriage return if it doesn't exist
        if msg[-1] != b'\r': 
            msg = msg + b'\r'
        
        # Write to serial
        self.serial.write(msg)
        
        
    def read(self):
        msg = self.serial.readall()
        msg = msg.decode('utf-8')
        return msg
    
    def echo(self, msg):
        self.write(msg)
        message = self.read()
        return message
    
if __name__=='__main__':
    vc = uPy('/dev/ttyACM0', baudrate=115200, timeout=.05)
    vc.write('b=1')
    print(vc.read())
    vc.write('b')
    print(vc.read())